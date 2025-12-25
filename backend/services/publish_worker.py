"""
发布Worker - RQ任务执行器（V3 - 集中日志版）
负责实际执行发布任务，具有完善的异常处理和集中的日志输出
"""
import logging
import time
import sys
import os
from datetime import datetime
from typing import Dict, Optional
from sqlalchemy.exc import OperationalError, IntegrityError
from contextlib import contextmanager

# 添加backend目录到path以便导入logger_config
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from models import PublishTask, PlatformAccount, PublishHistory, get_db_session
from services.user_rate_limiter import get_rate_limiter

# RQ Worker日志配置 - 确保日志写入统一的日志文件
def setup_worker_logger():
    """为RQ Worker设置日志，确保日志写入到logs目录"""
    from logging.handlers import RotatingFileHandler

    worker_logger = logging.getLogger(__name__)

    # 避免重复配置
    if worker_logger.handlers:
        return worker_logger

    worker_logger.setLevel(logging.INFO)
    worker_logger.propagate = False

    # 日志目录
    log_dir = os.path.join(BACKEND_DIR, '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)

    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-5s | WORKER   | %(name)-20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 写入all.log
    all_log_file = os.path.join(log_dir, 'all.log')
    all_handler = RotatingFileHandler(
        all_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    all_handler.setLevel(logging.DEBUG)
    all_handler.setFormatter(formatter)
    worker_logger.addHandler(all_handler)

    # 写入worker专属日志
    worker_log_file = os.path.join(log_dir, 'worker.log')
    worker_handler = RotatingFileHandler(
        worker_log_file,
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    worker_handler.setLevel(logging.DEBUG)
    worker_handler.setFormatter(formatter)
    worker_logger.addHandler(worker_handler)

    # 同时输出到控制台（方便调试）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    worker_logger.addHandler(console_handler)

    return worker_logger

# 初始化logger
logger = setup_worker_logger()


class TaskLogger:
    """任务日志记录器 - 集中管理日志输出"""

    def __init__(self, task_id: str):
        self.task_id = task_id
        self.logs = []
        self.start_time = datetime.now()

    def log(self, message: str, level: str = 'INFO'):
        """记录日志"""
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        elapsed = (datetime.now() - self.start_time).total_seconds()
        log_entry = f"[{timestamp}] [{elapsed:6.2f}s] [{level:5}] {message}"
        self.logs.append(log_entry)

        # 同时输出到标准日志
        if level == 'ERROR':
            logger.error(message)
        elif level == 'WARN':
            logger.warning(message)
        elif level == 'DEBUG':
            logger.debug(message)
        else:
            logger.info(message)

    def print_summary(self):
        """打印完整日志摘要"""
        separator = "=" * 80
        logger.info(f"\n{separator}")
        logger.info(f"任务执行日志 - TaskID: {self.task_id}")
        logger.info(separator)
        for log in self.logs:
            logger.info(log)
        logger.info(separator)
        logger.info(f"总耗时: {(datetime.now() - self.start_time).total_seconds():.2f}秒")
        logger.info(separator)


@contextmanager
def get_db_with_retry(task_log: TaskLogger, max_retries=3, retry_delay=1):
    """
    获取数据库Session的上下文管理器，支持重试

    Args:
        task_log: 任务日志记录器
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
                task_log.log(f"数据库连接失败，{retry_delay}秒后重试 (尝试 {attempt + 1}/{max_retries})", 'WARN')
                time.sleep(retry_delay)
            else:
                task_log.log(f"数据库连接失败，已达最大重试次数: {e}", 'ERROR')
                raise
        finally:
            if db:
                try:
                    db.close()
                except Exception as e:
                    task_log.log(f"关闭数据库连接失败: {e}", 'WARN')


def update_task_status(task_db_id: int, updates: Dict, task_log: TaskLogger, max_retries=3) -> bool:
    """
    更新任务状态（带重试机制）

    Args:
        task_db_id: 任务数据库ID
        updates: 要更新的字段字典
        task_log: 任务日志记录器
        max_retries: 最大重试次数

    Returns:
        是否更新成功
    """
    update_desc = ', '.join([f"{k}={v}" for k, v in updates.items() if k != 'error_message'])
    task_log.log(f"更新任务状态: {update_desc}")

    for attempt in range(max_retries):
        try:
            with get_db_with_retry(task_log) as db:
                task = db.query(PublishTask).filter(
                    PublishTask.id == task_db_id
                ).first()

                if not task:
                    task_log.log(f"任务不存在: DB_ID={task_db_id}", 'ERROR')
                    return False

                # 更新字段
                for key, value in updates.items():
                    setattr(task, key, value)

                db.commit()
                task_log.log(f"✓ 状态更新成功")
                return True

        except OperationalError as e:
            if '2013' in str(e):  # Lost connection
                if attempt < max_retries - 1:
                    task_log.log(f"MySQL连接丢失，{attempt + 1}秒后重试", 'WARN')
                    time.sleep(attempt + 1)
                    continue
            task_log.log(f"更新失败: {e}", 'ERROR')
            return False
        except Exception as e:
            task_log.log(f"更新失败: {e}", 'ERROR')
            return False

    return False


def get_task_info(task_db_id: int, task_log: TaskLogger) -> Optional[Dict]:
    """
    获取任务信息

    Args:
        task_db_id: 任务数据库ID
        task_log: 任务日志记录器

    Returns:
        任务信息字典，如果失败返回None
    """
    task_log.log(f"获取任务信息 (DB_ID={task_db_id})")

    try:
        with get_db_with_retry(task_log) as db:
            task = db.query(PublishTask).filter(
                PublishTask.id == task_db_id
            ).first()

            if not task:
                task_log.log(f"任务不存在", 'ERROR')
                return None

            info = {
                'id': task.id,
                'task_id': task.task_id,
                'user_id': task.user_id,
                'article_id': task.article_id,
                'article_title': task.article_title,
                'article_content': task.article_content,
                'platform': task.platform
            }

            task_log.log(f"✓ TaskID={task.task_id[:16]}..., User={task.user_id}, Platform={task.platform}")
            task_log.log(f"  标题: {task.article_title[:50]}...")
            task_log.log(f"  内容长度: {len(task.article_content)} 字符")

            return info
    except Exception as e:
        task_log.log(f"获取任务信息失败: {e}", 'ERROR')
        return None


def get_platform_account(user_id: int, platform: str, task_log: TaskLogger) -> Optional[Dict]:
    """
    获取平台账号信息

    Args:
        user_id: 用户ID
        platform: 平台名称
        task_log: 任务日志记录器

    Returns:
        账号信息字典
    """
    # 平台名称映射：兼容英文和中文平台名
    platform_mapping = {
        'zhihu': '知乎',
        'csdn': 'CSDN',
        'jianshu': '简书'
    }
    # 如果传入的是英文名，转换为中文名进行查询
    platform_query = platform_mapping.get(platform.lower(), platform) if platform else platform

    task_log.log(f"获取{platform_query}账号 (User={user_id})")

    try:
        with get_db_with_retry(task_log) as db:
            account = db.query(PlatformAccount).filter_by(
                user_id=user_id,
                platform=platform_query,
                status='active'
            ).first()

            if account:
                from encryption import decrypt_password
                task_log.log(f"✓ 找到账号: {account.username}")
                return {
                    'username': account.username,
                    'password': decrypt_password(account.password_encrypted) if account.password_encrypted else None
                }
            else:
                task_log.log(f"未找到账号，使用默认", 'WARN')
                return {
                    'username': f'user_{user_id}',
                    'password': None
                }
    except Exception as e:
        task_log.log(f"获取账号失败: {e}, 使用默认", 'WARN')
        return {
            'username': f'user_{user_id}',
            'password': None
        }


def publish_to_zhihu(title: str, content: str, username: str, password: Optional[str], task_log: TaskLogger) -> Dict:
    """
    发布到知乎（带异常处理）

    Args:
        title: 文章标题
        content: 文章内容
        username: 用户名
        password: 密码（可选）
        task_log: 任务日志记录器

    Returns:
        发布结果字典
    """
    task_log.log(f"开始发布到知乎")
    task_log.log(f"  账号: {username}")
    task_log.log(f"  标题: {title[:50]}...")
    task_log.log(f"  内容: {len(content)} 字符")
    task_log.log(f"  提供密码: {'是' if password else '否'}")

    try:
        from zhihu_auto_post_enhanced import post_article_to_zhihu

        publish_start = datetime.now()

        result = post_article_to_zhihu(
            username=username,
            title=title,
            content=content,
            password=password,
            topics=None,
            draft=False
        )

        publish_duration = (datetime.now() - publish_start).total_seconds()

        if result.get('success'):
            task_log.log(f"✓ 知乎发布成功 (耗时 {publish_duration:.2f}秒)")
            task_log.log(f"  文章URL: {result.get('url')}")
        else:
            task_log.log(f"✗ 知乎发布失败: {result.get('error', result.get('message'))}", 'ERROR')

        return result

    except ImportError as e:
        error_msg = f"导入知乎发布模块失败: {e}"
        task_log.log(error_msg, 'ERROR')
        return {'success': False, 'error': error_msg}

    except Exception as e:
        error_msg = f"知乎发布异常: {type(e).__name__}: {str(e)}"
        task_log.log(error_msg, 'ERROR')
        return {'success': False, 'error': error_msg}


def execute_publish_task(task_db_id: int) -> Dict:
    """
    执行发布任务(RQ Worker调用的函数) - V3集中日志版

    关键特性:
    1. 集中的日志输出 - 任务结束时统一打印完整日志
    2. 分段Session管理 - 不长时间持有数据库连接
    3. 完善的异常处理 - 每个步骤都有错误处理
    4. 自动重试机制 - 数据库操作失败自动重试

    Args:
        task_db_id: 任务数据库ID

    Returns:
        执行结果
    """
    # 创建临时日志记录器（TaskID稍后更新）
    task_log = TaskLogger(f"DB_ID:{task_db_id}")
    task_log.log("=" * 60)
    task_log.log("Worker开始执行任务")
    task_log.log("=" * 60)

    user_id = None

    try:
        # ===== 步骤1: 获取任务信息 =====
        task_log.log("")
        task_log.log("【步骤1/5】获取任务信息")

        task_info = get_task_info(task_db_id, task_log)
        if not task_info:
            task_log.log("任务获取失败，终止执行", 'ERROR')
            task_log.print_summary()
            return {'success': False, 'error': '任务不存在'}

        # 更新TaskLogger的task_id
        task_log.task_id = task_info['task_id']
        user_id = task_info['user_id']

        # ===== 步骤2: 更新状态为running =====
        task_log.log("")
        task_log.log("【步骤2/5】更新任务状态")

        success = update_task_status(task_db_id, {
            'status': 'running',
            'started_at': datetime.now(),
            'progress': 10
        }, task_log)

        if not success:
            raise Exception("更新任务状态为running失败")

        # ===== 步骤3: 获取平台账号 =====
        task_log.log("")
        task_log.log("【步骤3/5】获取平台账号")

        account = get_platform_account(user_id, task_info['platform'], task_log)
        if not account:
            raise Exception("获取平台账号失败")

        update_task_status(task_db_id, {'progress': 20}, task_log)

        # ===== 步骤4: 执行发布 =====
        task_log.log("")
        task_log.log("【步骤4/5】执行发布")

        if task_info['platform'] in ['zhihu', '知乎']:
            result = publish_to_zhihu(
                title=task_info['article_title'],
                content=task_info['article_content'],
                username=account['username'],
                password=account.get('password'),
                task_log=task_log
            )
        else:
            error_msg = f"不支持的平台: {task_info['platform']}"
            task_log.log(error_msg, 'ERROR')
            raise Exception(error_msg)

        update_task_status(task_db_id, {'progress': 90}, task_log)

        # ===== 步骤5: 更新最终结果 =====
        task_log.log("")
        task_log.log("【步骤5/5】更新最终结果")

        if result.get('success'):
            # 发布成功
            success = update_task_status(task_db_id, {
                'status': 'success',
                'result_url': result.get('url'),
                'progress': 100,
                'completed_at': datetime.now()
            }, task_log)

            if success:
                task_log.log("")
                task_log.log("✓✓✓ 任务执行成功！", 'INFO')
                task_log.log(f"文章URL: {result.get('url')}")

                # 保存到发布历史
                try:
                    db = get_db_session()

                    # 平台名称映射：内部使用英文，显示使用中文
                    platform_display = {
                        'zhihu': '知乎',
                        'csdn': 'CSDN',
                        'jianshu': '简书'
                    }
                    platform = platform_display.get(task_info['platform'], task_info['platform'])

                    history_record = PublishHistory(
                        user_id=task_info['user_id'],
                        article_id=task_info.get('article_id'),
                        platform=platform,
                        status='success',
                        url=result.get('url'),
                        message='发布成功',
                        article_title=task_info.get('article_title'),
                        article_content=task_info.get('article_content')
                    )
                    db.add(history_record)
                    db.commit()
                    task_log.log("✓ 发布历史已保存到数据库")
                    db.close()
                except Exception as he:
                    task_log.log(f"⚠️ 保存发布历史失败: {he}", 'WARN')
                    try:
                        db.rollback()
                        db.close()
                    except:
                        pass
            else:
                task_log.log("发布成功但状态更新失败", 'WARN')

            # 打印完整日志
            task_log.print_summary()

            return {
                'success': True,
                'task_id': task_info['task_id'],
                'url': result.get('url')
            }
        else:
            # 发布失败
            error_msg = result.get('error', '发布失败')
            raise Exception(error_msg)

    except Exception as e:
        task_log.log("")
        task_log.log("✗✗✗ 任务执行失败", 'ERROR')
        task_log.log(f"异常类型: {type(e).__name__}")
        task_log.log(f"异常信息: {str(e)}")

        # 更新失败状态
        if task_info:
            success = update_task_status(task_db_id, {
                'status': 'failed',
                'error_message': str(e)[:500],
                'completed_at': datetime.now()
            }, task_log)

            if not success:
                task_log.log("更新失败状态也失败了", 'ERROR')

        # 打印完整日志
        task_log.print_summary()

        return {
            'success': False,
            'error': str(e)
        }

    finally:
        # ===== 清理资源 =====
        if user_id:
            try:
                task_log.log("")
                task_log.log("释放限流令牌")
                rate_limiter = get_rate_limiter()
                rate_limiter.release(user_id)
                task_log.log("✓ 限流令牌已释放")
            except Exception as e:
                task_log.log(f"释放限流令牌失败: {e}", 'WARN')
