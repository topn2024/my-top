"""
发布重试API蓝图
处理失败发布的重试请求
"""
from flask import Blueprint, request, jsonify

# 从父目录导入
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth import login_required, get_current_user
from models import PublishHistory, Article, PlatformAccount, get_db_session
from logger_config import setup_logger, log_api_request
from encryption import decrypt_password
from datetime import datetime

# 初始化日志
logger = setup_logger(__name__)

# 创建蓝图
api_retry_bp = Blueprint('api_retry', __name__, url_prefix='/api')


@api_retry_bp.route('/retry_publish/<int:history_id>', methods=['POST'])
@login_required
@log_api_request("重试发布文章")
def retry_publish(history_id):
    """重试发布失败的文章"""
    try:
        user = get_current_user()
        db = get_db_session()

        try:
            # 获取发布历史记录
            history = db.query(PublishHistory).filter_by(
                id=history_id,
                user_id=user.id  # 确保只能重试自己的记录
            ).first()

            if not history:
                return jsonify({'success': False, 'error': '发布记录不存在'}), 404

            # 检查平台
            if history.platform != '知乎':
                return jsonify({'success': False, 'error': f'暂不支持重试{history.platform}平台'}), 400

            # 准备重新发布
            title = history.article_title
            content = history.article_content
            article_id = history.article_id

            # 如果有关联文章，从文章中获取内容
            if history.article:
                title = history.article.title
                content = history.article.content
                article_id = history.article.id
            elif not content:
                # 临时发布的文章且没有内容，无法重试
                return jsonify({
                    'success': False,
                    'error': '该记录无可用内容，无法重试。请重新选择文章发布'
                }), 400

            # 获取账号信息
            account = db.query(PlatformAccount).filter_by(
                id=history.account_id,
                user_id=user.id
            ).first()

            if not account:
                return jsonify({'success': False, 'error': '账号不存在或无权限'}), 404

            if not account.cookies:
                return jsonify({
                    'success': False,
                    'error': '账号Cookie已失效，请重新登录'
                }), 400

        finally:
            db.close()

        # 使用异步任务队列重试发布
        try:
            from services.task_queue_manager import get_task_manager

            task_manager = get_task_manager()

            # 创建发布任务
            task_id = task_manager.create_task(
                user_id=user.id,
                task_type='publish',
                platform=history.platform,
                data={
                    'account_id': account.id,
                    'article_id': article_id,
                    'title': title,
                    'content': content,
                    'retry_of': history_id  # 标记这是重试任务
                }
            )

            logger.info(f'Retry publish task created: {task_id} for history: {history_id}')

            return jsonify({
                'success': True,
                'message': '重试任务已创建',
                'task_id': task_id,
                'original_history_id': history_id
            })

        except ImportError:
            logger.warning('Task queue not available, using direct publish')

            # 降级方案：直接发布
            from publishers import PlatformPublisherFactory

            try:
                publisher = PlatformPublisherFactory.create_publisher(history.platform)

                # 设置账号cookie
                cookies = eval(account.cookies) if isinstance(account.cookies, str) else account.cookies
                publisher.set_cookies(cookies)

                # 发布文章
                success, publish_url, message = publisher.publish_article(
                    title=title,
                    content=content
                )

                # 关闭发布器
                publisher.close()

                # 更新发布历史
                db = get_db_session()
                try:
                    if success:
                        history.status = 'success'
                        history.publish_url = publish_url
                        history.retry_count = (history.retry_count or 0) + 1
                        history.published_at = datetime.now()
                        db.commit()

                        logger.info(f'Retry publish success: {publish_url}')

                        return jsonify({
                            'success': True,
                            'message': '重新发布成功',
                            'publish_url': publish_url,
                            'history_id': history_id
                        })
                    else:
                        history.status = 'failed'
                        history.error_message = message
                        history.retry_count = (history.retry_count or 0) + 1
                        db.commit()

                        logger.warning(f'Retry publish failed: {message}')

                        return jsonify({
                            'success': False,
                            'error': message or '发布失败'
                        }), 500

                finally:
                    db.close()

            except Exception as e:
                logger.error(f'Direct retry publish failed: {e}', exc_info=True)

                # 更新失败状态
                db = get_db_session()
                try:
                    history = db.query(PublishHistory).get(history_id)
                    if history:
                        history.status = 'failed'
                        history.error_message = str(e)
                        history.retry_count = (history.retry_count or 0) + 1
                        db.commit()
                finally:
                    db.close()

                return jsonify({'success': False, 'error': str(e)}), 500

    except Exception as e:
        logger.error(f'Retry publish failed: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
