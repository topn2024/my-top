"""
发布Worker - RQ任务执行器（增强版）
负责实际执行发布任务，具有完善的异常处理和重试机制
"""
import logging
import time
from datetime import datetime
from typing import Dict, Optional
from sqlalchemy.exc import OperationalError, IntegrityError
from contextlib import contextmanager

from models import PublishTask, PlatformAccount, get_db_session
from services.user_rate_limiter import get_rate_limiter

logger = logging.getLogger(__name__)


@contextmanager
def get_db_with_retry(max_retries=3, retry_delay=1):
    """
    获取数据库Session的上下文管理器，支持重试

    Args:
        max_retries: 最大重试次数
        retry_delay: 重试延迟（秒）

    Yields:
        数据库Session
    """
    db = None
    for attempt in range(max_retries):
        try:
            db = get_db_session()
            yield db
            break
        except OperationalError as e:
            if db:
                db.rollback()
                db.close()

            if attempt < max_retries - 1:
                logger.warning(f"数据库连接失败，{retry_delay}秒后重试 ({attempt + 1}/{max_retries}): {e}")
                time.sleep(retry_delay)
            else:
                logger.error(f"数据库连接失败，已达最大重试次数: {e}")
                raise
        finally:
            if db:
                try:
                    db.close()
                except Exception as e:
                    logger.error(f"关闭数据库连接失败: {e}")


def update_task_status(task_db_id: int, updates: Dict, max_retries=3) -> bool:
    """
    更新任务状态（带重试机制）

    Args:
        task_db_id: 任务数据库ID
        updates: 要更新的字段字典
        max_retries: 最大重试次数

    Returns:
        是否更新成功
    """
    for attempt in range(max_retries):
        try:
            with get_db_with_retry() as db:
                task = db.query(PublishTask).filter(
                    PublishTask.id == task_db_id
                ).first()

                if not task:
                    logger.error(f"任务不存在: DB_ID={task_db_id}")
                    return False

                # 更新字段
                for key, value in updates.items():
                    setattr(task, key, value)

                db.commit()
                logger.debug(f"任务状态更新成功: {updates}")
                return True

        except OperationalError as e:
            if '2013' in str(e):  # Lost connection
                if attempt < max_retries - 1:
                    logger.warning(f"MySQL连接丢失，{attempt + 1}秒后重试 ({attempt + 1}/{max_retries})")
                    time.sleep(attempt + 1)
                    continue
            logger.error(f"更新任务状态失败: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"更新任务状态失败: {e}", exc_info=True)
            return False

    return False


def get_task_info(task_db_id: int) -> Optional[Dict]:
    """
    获取任务信息

    Args:
        task_db_id: 任务数据库ID

    Returns:
        任务信息字典，如果失败返回None
    """
    try:
        with get_db_with_retry() as db:
            task = db.query(PublishTask).filter(
                PublishTask.id == task_db_id
            ).first()

            if not task:
                logger.error(f"任务不存在: DB_ID={task_db_id}")
                return None

            return {
                'id': task.id,
                'task_id': task.task_id,
                'user_id': task.user_id,
                'article_id': task.article_id,
                'article_title': task.article_title,
                'article_content': task.article_content,
                'platform': task.platform
            }
    except Exception as e:
        logger.error(f"获取任务信息失败: {e}", exc_info=True)
        return None


def get_platform_account(user_id: int, platform: str = '知乎') -> Optional[Dict]:
    """
    获取平台账号信息

    Args:
        user_id: 用户ID
        platform: 平台名称

    Returns:
        账号信息字典，如果失败返回None
    """
    try:
        with get_db_with_retry() as db:
            account = db.query(PlatformAccount).filter_by(
                user_id=user_id,
                platform=platform,
                status='active'
            ).first()

            if account:
                from encryption import decrypt_password
                return {
                    'username': account.username,
                    'password': decrypt_password(account.password_encrypted) if account.password_encrypted else None
                }
            else:
                logger.warning(f"未找到{platform}账号: user_id={user_id}")
                return {
                    'username': f'user_{user_id}',
                    'password': None
                }
    except Exception as e:
        logger.error(f"获取平台账号失败: {e}", exc_info=True)
        return {
            'username': f'user_{user_id}',
            'password': None
        }


def publish_to_zhihu(title: str, content: str, username: str, password: Optional[str] = None) -> Dict:
    """
    发布到知乎（带异常处理）

    Args:
        title: 文章标题
        content: 文章内容
        username: 用户名
        password: 密码（可选）

    Returns:
        发布结果字典
    """
    try:
        from zhihu_auto_post_enhanced import post_article_to_zhihu

        logger.info(f"[知乎发布] 开始发布: 标题={title[:30]}...")

        result = post_article_to_zhihu(
            username=username,
            title=title,
            content=content,
            password=password,
            topics=None,
            draft=False
        )

        logger.info(f"[知乎发布] 发布完成: {result}")
        return result

    except ImportError as e:
        error_msg = f"导入知乎发布模块失败: {e}"
        logger.error(f"[知乎发布] {error_msg}")
        return {'success': False, 'error': error_msg}

    except Exception as e:
        error_msg = f"知乎发布异常: {type(e).__name__}: {str(e)}"
        logger.error(f"[知乎发布] {error_msg}", exc_info=True)
        return {'success': False, 'error': error_msg}


def execute_publish_task(task_db_id: int) -> Dict:
    """
    执行发布任务(RQ Worker调用的函数) - 增强版

    关键改进:
    1. 分段获取数据库Session，不长时间持有连接
    2. 完善的异常处理和重试机制
    3. 确保限流令牌一定被释放
    4. 详细的日志记录

    Args:
        task_db_id: 任务数据库ID

    Returns:
        执行结果
    """
    logger.info(f"[发布流程-Worker] ========== Worker开始执行任务 ==========")
    logger.info(f"[发布流程-Worker] 任务DB ID: {task_db_id}")

    start_time = datetime.now()
    task_info = None
    user_id = None

    try:
        # ===== 阶段1: 获取任务信息并更新为running =====
        logger.info(f"[发布流程-Worker] 阶段1: 获取任务信息")

        task_info = get_task_info(task_db_id)
        if not task_info:
            return {'success': False, 'error': '任务不存在'}

        user_id = task_info['user_id']
        logger.info(f"[发布流程-Worker] 任务信息: TaskID={task_info['task_id']}, User={user_id}, Platform={task_info['platform']}")
        logger.info(f"[发布流程-Worker] 文章标题: {task_info['article_title'][:50]}")
        logger.info(f"[发布流程-Worker] 文章长度: {len(task_info['article_content'])} 字符")

        # 更新状态为running
        success = update_task_status(task_db_id, {
            'status': 'running',
            'started_at': datetime.now(),
            'progress': 10
        })

        if not success:
            logger.error(f"[发布流程-Worker] 更新任务状态为running失败")
            return {'success': False, 'error': '更新任务状态失败'}

        logger.info(f"[发布流程-Worker] 任务状态已更新为 running")

        # ===== 阶段2: 获取平台账号信息 =====
        logger.info(f"[发布流程-Worker] 阶段2: 获取平台账号")

        account = get_platform_account(user_id, task_info['platform'])
        if not account:
            raise Exception("获取平台账号失败")

        logger.info(f"[发布流程-Worker] 使用账号: {account['username']}")

        # 更新进度
        update_task_status(task_db_id, {'progress': 20})

        # ===== 阶段3: 执行发布（不持有数据库连接）=====
        logger.info(f"[发布流程-Worker] 阶段3: 执行发布")

        if task_info['platform'] in ['zhihu', '知乎']:
            publish_start_time = datetime.now()

            result = publish_to_zhihu(
                title=task_info['article_title'],
                content=task_info['article_content'],
                username=account['username'],
                password=account.get('password')
            )

            publish_duration = (datetime.now() - publish_start_time).total_seconds()
            logger.info(f"[发布流程-Worker] 发布耗时: {publish_duration:.2f}秒")
        else:
            error_msg = f"不支持的平台: {task_info['platform']}"
            logger.error(f"[发布流程-Worker] {error_msg}")
            raise Exception(error_msg)

        # 更新进度
        update_task_status(task_db_id, {'progress': 90})

        # ===== 阶段4: 更新最终结果 =====
        logger.info(f"[发布流程-Worker] 阶段4: 更新最终结果")

        total_duration = (datetime.now() - start_time).total_seconds()

        if result.get('success'):
            # 发布成功
            success = update_task_status(task_db_id, {
                'status': 'success',
                'result_url': result.get('url'),
                'progress': 100,
                'completed_at': datetime.now()
            })

            if success:
                logger.info(f"[发布流程-Worker] ✓ 任务执行成功!")
                logger.info(f"[发布流程-Worker] TaskID: {task_info['task_id']}")
                logger.info(f"[发布流程-Worker] 文章URL: {result.get('url')}")
                logger.info(f"[发布流程-Worker] 总耗时: {total_duration:.2f}秒")
            else:
                logger.warning(f"[发布流程-Worker] 发布成功但数据库更新失败")

            return {
                'success': True,
                'task_id': task_info['task_id'],
                'url': result.get('url')
            }
        else:
            # 发布失败
            error_msg = result.get('error', '发布失败')
            logger.error(f"[发布流程-Worker] ✗ 发布失败: {error_msg}")
            raise Exception(error_msg)

    except Exception as e:
        logger.error(f"[发布流程-Worker] ========== Worker任务失败 ==========")
        logger.error(f"[发布流程-Worker] 异常类型: {type(e).__name__}")
        logger.error(f"[发布流程-Worker] 异常信息: {e}", exc_info=True)

        # 更新失败状态（带重试）
        if task_info:
            total_duration = (datetime.now() - start_time).total_seconds()

            success = update_task_status(task_db_id, {
                'status': 'failed',
                'error_message': str(e)[:500],  # 限制错误信息长度
                'completed_at': datetime.now()
            })

            if success:
                logger.warning(f"[发布流程-Worker] 任务状态已更新为 failed")
                logger.info(f"[发布流程-Worker] 失败耗时: {total_duration:.2f}秒")
            else:
                logger.error(f"[发布流程-Worker] 更新失败状态也失败了！")

        return {
            'success': False,
            'error': str(e)
        }

    finally:
        # ===== 阶段5: 清理资源 =====
        logger.debug(f"[发布流程-Worker] 阶段5: 清理资源")

        # 释放限流令牌（确保一定执行）
        if user_id:
            try:
                logger.debug(f"[发布流程-Worker] 释放用户 {user_id} 的限流令牌")
                rate_limiter = get_rate_limiter()
                rate_limiter.release(user_id)
            except Exception as e:
                logger.error(f"[发布流程-Worker] 释放限流令牌失败: {e}")

        logger.info(f"[发布流程-Worker] ========== Worker任务完成 ==========")
