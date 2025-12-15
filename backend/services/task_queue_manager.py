"""
任务队列管理器
负责创建、管理发布任务，并将任务入队到RQ
"""
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger_config import setup_logger, log_service_call
import uuid
from typing import Dict, List, Optional
from datetime import datetime
import redis
from rq import Queue
from rq.job import Job

from models import PublishTask, get_db_session
from services.user_rate_limiter import get_rate_limiter

logger = setup_logger(__name__)


class TaskQueueManager:
    """任务队列管理器"""

    def __init__(self, redis_client: redis.Redis = None):
        """
        初始化任务队列管理器

        Args:
            redis_client: Redis客户端实例
        """
        if redis_client is None:
            # 使用默认Redis连接
            self.redis = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=False  # RQ需要bytes模式
            )
        else:
            self.redis = redis_client

        # 创建默认队列
        self.default_queue = Queue('default', connection=self.redis)

        # 获取限流器
        self.rate_limiter = get_rate_limiter()

        logger.info("任务队列管理器初始化完成")

    def get_user_queue(self, user_id: int) -> Queue:
        """
        获取用户专属队列

        Args:
            user_id: 用户ID

        Returns:
            RQ Queue实例
        """
        queue_name = f'user:{user_id}'
        return Queue(queue_name, connection=self.redis)


    @log_service_call("创建发布任务")
    def create_publish_task(
        self,
        user_id: int,
        article_title: str,
        article_content: str,
        platform: str = 'zhihu',
        article_id: Optional[int] = None
    ) -> Dict:
        """
        创建发布任务

        Args:
            user_id: 用户ID
            article_title: 文章标题
            article_content: 文章内容
            platform: 发布平台
            article_id: 文章ID(可选)

        Returns:
            任务信息字典
        """
        logger.info(f'[发布流程-队列] 创建发布任务: user={user_id}, title={article_title[:30]}, platform={platform}')

        try:
            # 1. 检查限流
            logger.debug(f'[发布流程-队列] 检查用户 {user_id} 的限流状态')
            if not self.rate_limiter.acquire(user_id):
                stats = self.rate_limiter.get_user_stats(user_id)
                logger.warning(f'[发布流程-队列] 用户 {user_id} 触发限流: {stats}')
                return {
                    'success': False,
                    'error': '超过限流限制',
                    'message': f'当前并发任务: {stats["concurrent_tasks"]}/{stats["max_concurrent_tasks"]}, '
                              f'最近1分钟任务数: {stats["tasks_in_last_minute"]}/{stats["max_tasks_per_minute"]}',
                    'stats': stats
                }

            logger.debug(f'[发布流程-队列] 限流检查通过，开始创建任务')

            # 2. 生成任务ID
            task_id = str(uuid.uuid4())
            logger.info(f'[发布流程-队列] 生成任务ID: {task_id}')

            # 3. 创建数据库记录
            logger.debug(f'[发布流程-队列] 创建任务数据库记录')
            db = get_db_session()
            try:
                db_task = PublishTask(
                    task_id=task_id,
                    user_id=user_id,
                    article_id=article_id,
                    article_title=article_title,
                    article_content=article_content,
                    platform=platform,
                    status='pending'
                )
                db.add(db_task)
                db.commit()
                db.refresh(db_task)

                task_db_id = db_task.id
                logger.info(f'[发布流程-队列] 数据库记录创建成功: DB_ID={task_db_id}, TaskID={task_id}')

            except Exception as e:
                db.rollback()
                logger.error(f"[发布流程-队列] 创建任务数据库记录失败: {e}", exc_info=True)
                # 释放限流令牌
                self.rate_limiter.release(user_id)
                return {
                    'success': False,
                    'error': '创建任务失败',
                    'message': str(e)
                }
            finally:
                db.close()

            # 4. 创建RQ任务
            try:
                queue = self.get_user_queue(user_id)
                logger.info(f'[发布流程-队列] 准备将任务加入队列: {queue.name}')

                # 导入worker函数
                from services.publish_worker import execute_publish_task

                job = queue.enqueue(
                    execute_publish_task,
                    task_db_id=task_db_id,
                    job_id=task_id,
                    job_timeout='10m',  # 任务超时时间10分钟
                    result_ttl=3600,  # 结果保留1小时
                    failure_ttl=86400  # 失败记录保留24小时
                )

                logger.info(f'[发布流程-队列] RQ任务已入队: job_id={job.id}, queue={queue.name}')

                # 5. 更新任务状态为已入队
                db = get_db_session()
                try:
                    db_task = db.query(PublishTask).filter(
                        PublishTask.id == task_db_id
                    ).first()

                    if db_task:
                        db_task.status = 'queued'
                        db.commit()
                        logger.debug(f'[发布流程-队列] 任务状态更新为 queued')
                except Exception as e:
                    logger.error(f"[发布流程-队列] 更新任务状态失败: {e}")
                    db.rollback()
                finally:
                    db.close()

                logger.info(f"[发布流程-队列] 任务创建成功: {task_id}, user={user_id}, queue={queue.name}")

                return {
                    'success': True,
                    'task_id': task_id,
                    'status': 'queued',
                    'message': '任务已创建并入队'
                }

            except Exception as e:
                logger.error(f"[发布流程-队列] 创建RQ任务失败: {e}", exc_info=True)

                # 更新数据库状态为失败
                db = get_db_session()
                try:
                    db_task = db.query(PublishTask).filter(
                        PublishTask.id == task_db_id
                    ).first()
                    if db_task:
                        db_task.status = 'failed'
                        db_task.error_message = f"入队失败: {str(e)}"
                        db.commit()
                        logger.warning(f'[发布流程-队列] 任务状态更新为 failed')
                finally:
                    db.close()

                # 释放限流令牌
                self.rate_limiter.release(user_id)

                return {
                    'success': False,
                    'error': '任务入队失败',
                    'message': str(e)
                }

        except Exception as e:
            logger.error(f"创建任务失败: {e}", exc_info=True)
            return {
                'success': False,
                'error': '创建任务失败',
                'message': str(e)
            }


    @log_service_call("批量创建任务")
    def create_batch_tasks(
        self,
        user_id: int,
        articles: List[Dict],
        platform: str = 'zhihu'
    ) -> Dict:
        """
        批量创建发布任务

        Args:
            user_id: 用户ID
            articles: 文章列表 [{'title': '', 'content': '', 'article_id': 1}, ...]
            platform: 发布平台

        Returns:
            批量创建结果
        """
        results = []
        success_count = 0
        failed_count = 0

        for article in articles:
            result = self.create_publish_task(
                user_id=user_id,
                article_title=article.get('title', ''),
                article_content=article.get('content', ''),
                platform=platform,
                article_id=article.get('article_id')
            )

            if result['success']:
                success_count += 1
            else:
                failed_count += 1

            results.append({
                'article_title': article.get('title', '')[:50],
                'result': result
            })

        return {
            'success': failed_count == 0,
            'total': len(articles),
            'success_count': success_count,
            'failed_count': failed_count,
            'results': results
        }


    @log_service_call("查询任务状态")
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态信息
        """
        try:
            db = get_db_session()
            try:
                task = db.query(PublishTask).filter(
                    PublishTask.task_id == task_id
                ).first()

                if not task:
                    return None

                return task.to_dict()

            finally:
                db.close()

        except Exception as e:
            logger.error(f"获取任务状态失败: {e}", exc_info=True)
            return None

    def get_user_tasks(
        self,
        user_id: int,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Dict:
        """
        获取用户的任务列表

        Args:
            user_id: 用户ID
            status: 任务状态过滤
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            任务列表和统计信息
        """
        try:
            db = get_db_session()
            try:
                query = db.query(PublishTask).filter(
                    PublishTask.user_id == user_id
                )

                if status:
                    query = query.filter(PublishTask.status == status)

                # 统计总数
                total = query.count()

                # 获取任务列表
                tasks = query.order_by(
                    PublishTask.created_at.desc()
                ).limit(limit).offset(offset).all()

                # 统计各状态任务数
                stats = {
                    'pending': db.query(PublishTask).filter(
                        PublishTask.user_id == user_id,
                        PublishTask.status == 'pending'
                    ).count(),
                    'queued': db.query(PublishTask).filter(
                        PublishTask.user_id == user_id,
                        PublishTask.status == 'queued'
                    ).count(),
                    'running': db.query(PublishTask).filter(
                        PublishTask.user_id == user_id,
                        PublishTask.status == 'running'
                    ).count(),
                    'success': db.query(PublishTask).filter(
                        PublishTask.user_id == user_id,
                        PublishTask.status == 'success'
                    ).count(),
                    'failed': db.query(PublishTask).filter(
                        PublishTask.user_id == user_id,
                        PublishTask.status == 'failed'
                    ).count(),
                }

                return {
                    'success': True,
                    'total': total,
                    'tasks': [task.to_dict() for task in tasks],
                    'stats': stats
                }

            finally:
                db.close()

        except Exception as e:
            logger.error(f"获取用户任务列表失败: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }


    @log_service_call("取消任务")
    def cancel_task(self, task_id: str, user_id: int) -> Dict:
        """
        取消任务

        Args:
            task_id: 任务ID
            user_id: 用户ID(用于权限验证)

        Returns:
            取消结果
        """
        try:
            db = get_db_session()
            try:
                task = db.query(PublishTask).filter(
                    PublishTask.task_id == task_id,
                    PublishTask.user_id == user_id
                ).first()

                if not task:
                    return {
                        'success': False,
                        'error': '任务不存在或无权限'
                    }

                # 只能取消pending或queued状态的任务
                if task.status not in ['pending', 'queued']:
                    return {
                        'success': False,
                        'error': f'任务状态为{task.status}，无法取消'
                    }

                # 尝试取消RQ任务
                try:
                    job = Job.fetch(task_id, connection=self.redis)
                    job.cancel()
                except Exception as e:
                    logger.warning(f"取消RQ任务失败: {e}")

                # 更新数据库状态
                task.status = 'cancelled'
                task.completed_at = datetime.now()
                db.commit()

                # 释放限流令牌
                self.rate_limiter.release(user_id)

                logger.info(f"任务已取消: {task_id}")

                return {
                    'success': True,
                    'message': '任务已取消'
                }

            finally:
                db.close()

        except Exception as e:
            logger.error(f"取消任务失败: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }


    @log_service_call("重试任务")
    def retry_task(self, task_id: str, user_id: int) -> Dict:
        """
        重试失败的任务

        Args:
            task_id: 任务ID
            user_id: 用户ID

        Returns:
            重试结果
        """
        try:
            db = get_db_session()
            try:
                task = db.query(PublishTask).filter(
                    PublishTask.task_id == task_id,
                    PublishTask.user_id == user_id
                ).first()

                if not task:
                    return {
                        'success': False,
                        'error': '任务不存在或无权限'
                    }

                # 只能重试失败的任务
                if task.status != 'failed':
                    return {
                        'success': False,
                        'error': f'任务状态为{task.status}，无法重试'
                    }

                # 检查重试次数
                if task.retry_count >= task.max_retries:
                    return {
                        'success': False,
                        'error': f'已达最大重试次数({task.max_retries})'
                    }

                # 增加重试计数
                task.retry_count += 1
                task.status = 'pending'
                task.error_message = None
                db.commit()

                # 重新入队
                queue = self.get_user_queue(user_id)
                from services.publish_worker import execute_publish_task

                job = queue.enqueue(
                    execute_publish_task,
                    task_db_id=task.id,
                    job_id=task_id,
                    job_timeout='10m'
                )

                task.status = 'queued'
                db.commit()

                logger.info(f"任务重试: {task_id}, 第{task.retry_count}次")

                return {
                    'success': True,
                    'message': f'任务已重新入队(第{task.retry_count}次重试)'
                }

            finally:
                db.close()

        except Exception as e:
            logger.error(f"重试任务失败: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def get_queue_stats(self) -> Dict:
        """
        获取队列统计信息

        Returns:
            队列统计信息
        """
        try:
            stats = {
                'default_queue': {
                    'name': 'default',
                    'count': len(self.default_queue),
                    'failed_count': self.default_queue.failed_job_registry.count
                },
                'user_queues': []
            }

            # 获取所有用户队列
            # 这里简化处理，实际可以扫描Redis获取所有队列
            return stats

        except Exception as e:
            logger.error(f"获取队列统计失败: {e}", exc_info=True)
            return {
                'error': str(e)
            }

    def clear_tasks(
        self,
        user_id: int,
        task_ids: Optional[List[str]] = None,
        status_filter: Optional[List[str]] = None
    ) -> Dict:
        """
        清理任务（批量删除）

        Args:
            user_id: 用户ID（用于权限验证）
            task_ids: 要清理的任务ID列表（如果为None则根据status_filter清理）
            status_filter: 状态过滤器，可以是['success', 'failed', 'cancelled']等

        Returns:
            清理结果
        """
        try:
            db = get_db_session()
            try:
                deleted_count = 0
                failed_count = 0
                errors = []

                # 情况1: 清理指定的任务ID列表
                if task_ids:
                    for task_id in task_ids:
                        try:
                            task = db.query(PublishTask).filter(
                                PublishTask.task_id == task_id,
                                PublishTask.user_id == user_id
                            ).first()

                            if not task:
                                errors.append(f"任务 {task_id} 不存在或无权限")
                                failed_count += 1
                                continue

                            # 不允许删除正在运行的任务
                            if task.status in ['pending', 'queued', 'running']:
                                errors.append(f"任务 {task_id} 状态为 {task.status}，无法删除，请先取消")
                                failed_count += 1
                                continue

                            # 尝试从Redis中清理RQ任务（如果存在）
                            try:
                                job = Job.fetch(task_id, connection=self.redis)
                                job.delete()
                            except Exception as e:
                                logger.debug(f"清理RQ任务失败（可能已不存在）: {e}")

                            # 删除数据库记录
                            db.delete(task)
                            deleted_count += 1

                        except Exception as e:
                            logger.error(f"删除任务 {task_id} 失败: {e}", exc_info=True)
                            errors.append(f"删除任务 {task_id} 失败: {str(e)}")
                            failed_count += 1

                # 情况2: 根据状态过滤批量清理
                elif status_filter:
                    query = db.query(PublishTask).filter(
                        PublishTask.user_id == user_id,
                        PublishTask.status.in_(status_filter)
                    )

                    tasks_to_delete = query.all()

                    for task in tasks_to_delete:
                        try:
                            # 尝试从Redis中清理RQ任务
                            try:
                                job = Job.fetch(task.task_id, connection=self.redis)
                                job.delete()
                            except Exception as e:
                                logger.debug(f"清理RQ任务失败（可能已不存在）: {e}")

                            # 删除数据库记录
                            db.delete(task)
                            deleted_count += 1

                        except Exception as e:
                            logger.error(f"删除任务失败: {e}", exc_info=True)
                            failed_count += 1

                else:
                    return {
                        'success': False,
                        'error': '必须指定task_ids或status_filter参数'
                    }

                # 提交更改
                db.commit()

                logger.info(f"清理任务完成: user={user_id}, 删除={deleted_count}, 失败={failed_count}")

                return {
                    'success': True,
                    'deleted_count': deleted_count,
                    'failed_count': failed_count,
                    'errors': errors if errors else None,
                    'message': f'成功清理 {deleted_count} 个任务' + (f'，{failed_count} 个失败' if failed_count > 0 else '')
                }

            except Exception as e:
                db.rollback()
                logger.error(f"清理任务失败: {e}", exc_info=True)
                return {
                    'success': False,
                    'error': '清理任务失败',
                    'message': str(e)
                }
            finally:
                db.close()

        except Exception as e:
            logger.error(f"清理任务失败: {e}", exc_info=True)
            return {
                'success': False,
                'error': '清理任务失败',
                'message': str(e)
            }


# 全局TaskQueueManager实例
_task_manager = None


def get_task_manager(redis_client: redis.Redis = None) -> TaskQueueManager:
    """
    获取全局TaskQueueManager实例(单例模式)

    Args:
        redis_client: Redis客户端

    Returns:
        TaskQueueManager实例
    """
    global _task_manager

    if _task_manager is None:
        _task_manager = TaskQueueManager(redis_client)

    return _task_manager
