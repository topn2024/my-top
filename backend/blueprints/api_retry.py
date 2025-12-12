#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重试发布API接口 - 添加到api.py的新路由
"""

@api_bp.route('/retry_publish/<int:history_id>', methods=['POST'])
@login_required
def retry_publish(history_id):
    """重试发布失败的文章"""
    from services.publish_service import PublishService
    from models import get_db_session, PublishHistory

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
        title = history.title
        article_id = history.article_id

        # 如果有关联文章，从文章中获取内容
        if history.article:
            title = history.article.title
            content = history.article.content
        else:
            # 临时发布的文章，无法重试
            return jsonify({
                'success': False,
                'error': '该记录为临时发布，无法重试。请重新选择文章发布'
            }), 400

        logger.info(f'Retry publishing article: {title} to 知乎 (history_id={history_id})')

        # 调用发布服务
        publish_service = PublishService(config)
        success, message, url = publish_service.publish_to_zhihu(
            user_id=user.id,
            title=title,
            content=content,
            article_id=article_id,
            draft=False
        )

        if success:
            return jsonify({
                'success': True,
                'message': message or '重新发布成功',
                'url': url
            })
        else:
            return jsonify({
                'success': False,
                'error': message or '重新发布失败'
            }), 500

    except Exception as e:
        logger.error(f'Retry publish failed: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()
