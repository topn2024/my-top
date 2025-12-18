"""
任务API接口
提供REST API用于管理发布任务
"""
from flask import Blueprint, request, jsonify, session
from functools import wraps
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.task_queue_manager import get_task_manager
from logger_config import setup_logger, log_api_request
from auth import login_required

logger = setup_logger(__name__)

# 创建Blueprint
task_bp = Blueprint('task_api', __name__)


@task_bp.route('/create', methods=['POST'])
@login_required
@log_api_request("创建发布任务")
def create_task():
    """
    创建单个发布任务

    请求体:
    {
        "title": "文章标题",
        "content": "文章内容",
        "platform": "zhihu",  // 可选，默认zhihu
        "article_id": 123     // 可选
    }

    返回:
    {
        "success": true,
        "task_id": "uuid",
        "status": "queued",
        "message": "任务已创建并入队"
    }
    """
    try:
        data = request.get_json()

        # 验证必需字段
        if not data.get('title'):
            return jsonify({
                'success': False,
                'error': '缺少title字段'
            }), 400

        if not data.get('content'):
            return jsonify({
                'success': False,
                'error': '缺少content字段'
            }), 400

        # 获取用户ID
        user_id = session.get('user_id')

        # 创建任务
        manager = get_task_manager()
        result = manager.create_publish_task(
            user_id=user_id,
            article_title=data['title'],
            article_content=data['content'],
            platform=data.get('platform', 'zhihu'),
            article_id=data.get('article_id')
        )

        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"创建任务失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': '创建任务失败',
            'message': str(e)
        }), 500


@task_bp.route('/create_batch', methods=['POST'])
@login_required
@log_api_request("批量创建发布任务")
def create_batch_tasks():
    """
    批量创建发布任务

    请求体:
    {
        "articles": [
            {
                "title": "文章1",
                "content": "内容1",
                "article_id": 1
            },
            {
                "title": "文章2",
                "content": "内容2",
                "article_id": 2
            }
        ],
        "platform": "zhihu"  // 可选，默认zhihu
    }

    返回:
    {
        "success": true,
        "total": 2,
        "success_count": 2,
        "failed_count": 0,
        "results": [...]
    }
    """
    try:
        data = request.get_json()

        # 验证必需字段
        if not data.get('articles'):
            return jsonify({
                'success': False,
                'error': '缺少articles字段'
            }), 400

        if not isinstance(data['articles'], list):
            return jsonify({
                'success': False,
                'error': 'articles必须是数组'
            }), 400

        # 获取用户ID
        user_id = session.get('user_id')

        # 批量创建任务
        manager = get_task_manager()
        result = manager.create_batch_tasks(
            user_id=user_id,
            articles=data['articles'],
            platform=data.get('platform', 'zhihu')
        )

        return jsonify(result), 201

    except Exception as e:
        logger.error(f"批量创建任务失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': '批量创建任务失败',
            'message': str(e)
        }), 500


@task_bp.route('/<task_id>', methods=['GET'])
@login_required
@log_api_request("查询任务状态")
def get_task_status(task_id):
    """
    查询任务状态

    返回:
    {
        "id": 1,
        "task_id": "uuid",
        "user_id": 1,
        "article_title": "标题",
        "platform": "zhihu",
        "status": "running",
        "progress": 50,
        "result_url": null,
        "error_message": null,
        "created_at": "2024-01-01 00:00:00",
        ...
    }
    """
    try:
        manager = get_task_manager()
        task = manager.get_task_status(task_id)

        if task is None:
            return jsonify({
                'success': False,
                'error': '任务不存在'
            }), 404

        # 验证权限（只能查看自己的任务）
        if task['user_id'] != session.get('user_id'):
            return jsonify({
                'success': False,
                'error': '无权限查看此任务'
            }), 403

        return jsonify({
            'success': True,
            'task': task
        })

    except Exception as e:
        logger.error(f"查询任务状态失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': '查询任务状态失败',
            'message': str(e)
        }), 500


@task_bp.route('/list', methods=['GET'])
@login_required
@log_api_request("获取任务列表")
def get_task_list():
    """
    获取任务列表

    查询参数:
    - status: 任务状态过滤（pending/queued/running/success/failed/cancelled）
    - limit: 返回数量，默认20
    - offset: 偏移量，默认0

    返回:
    {
        "success": true,
        "total": 100,
        "tasks": [...],
        "stats": {
            "pending": 10,
            "queued": 5,
            "running": 3,
            "success": 80,
            "failed": 2
        }
    }
    """
    try:
        # 获取查询参数
        status = request.args.get('status')
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))

        # 验证参数
        if limit > 100:
            limit = 100

        # 获取用户ID
        user_id = session.get('user_id')

        # 查询任务列表
        manager = get_task_manager()
        result = manager.get_user_tasks(
            user_id=user_id,
            status=status,
            limit=limit,
            offset=offset
        )

        return jsonify(result)

    except Exception as e:
        logger.error(f"获取任务列表失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': '获取任务列表失败',
            'message': str(e)
        }), 500


@task_bp.route('/<task_id>/cancel', methods=['POST'])
@login_required
@log_api_request("取消任务")
def cancel_task(task_id):
    """
    取消任务

    只能取消pending或queued状态的任务

    返回:
    {
        "success": true,
        "message": "任务已取消"
    }
    """
    try:
        user_id = session.get('user_id')

        manager = get_task_manager()
        result = manager.cancel_task(task_id, user_id)

        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"取消任务失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': '取消任务失败',
            'message': str(e)
        }), 500


@task_bp.route('/<task_id>/retry', methods=['POST'])
@login_required
@log_api_request("重试失败的任务")
def retry_task(task_id):
    """
    重试失败的任务

    只能重试failed状态的任务，且未超过最大重试次数

    返回:
    {
        "success": true,
        "message": "任务已重新入队(第1次重试)"
    }
    """
    try:
        user_id = session.get('user_id')

        manager = get_task_manager()
        result = manager.retry_task(task_id, user_id)

        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"重试任务失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': '重试任务失败',
            'message': str(e)
        }), 500


@task_bp.route('/stats', methods=['GET'])
@login_required
@log_api_request("获取任务统计信息")
def get_stats():
    """
    获取用户的限流统计信息

    返回:
    {
        "success": true,
        "concurrent_tasks": 3,
        "max_concurrent_tasks": 10,
        "tasks_in_last_minute": 5,
        "max_tasks_per_minute": 20
    }
    """
    try:
        user_id = session.get('user_id')

        from backend.services.user_rate_limiter import get_rate_limiter
        limiter = get_rate_limiter()
        stats = limiter.get_user_stats(user_id)

        return jsonify({
            'success': True,
            **stats
        })

    except Exception as e:
        logger.error(f"获取统计信息失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': '获取统计信息失败',
            'message': str(e)
        }), 500


@task_bp.route('/clear', methods=['POST'])
@login_required
@log_api_request("批量清理任务")
def clear_tasks():
    """
    清理任务（批量删除）

    请求体:
    {
        "task_ids": ["uuid1", "uuid2"],  // 可选，要删除的任务ID列表
        "status_filter": ["success", "failed", "cancelled"]  // 可选，按状态批量删除
    }

    返回:
    {
        "success": true,
        "deleted_count": 10,
        "failed_count": 0,
        "message": "成功清理 10 个任务"
    }
    """
    try:
        data = request.get_json() or {}
        user_id = session.get('user_id')

        # 获取参数
        task_ids = data.get('task_ids')
        status_filter = data.get('status_filter')

        # 验证至少提供一个参数
        if not task_ids and not status_filter:
            return jsonify({
                'success': False,
                'error': '必须指定task_ids或status_filter参数'
            }), 400

        # 验证status_filter的值
        if status_filter:
            valid_statuses = ['pending', 'queued', 'running', 'success', 'failed', 'cancelled']
            invalid_statuses = [s for s in status_filter if s not in valid_statuses]
            if invalid_statuses:
                return jsonify({
                    'success': False,
                    'error': f'无效的状态值: {invalid_statuses}'
                }), 400

        # 调用清理方法
        manager = get_task_manager()
        result = manager.clear_tasks(
            user_id=user_id,
            task_ids=task_ids,
            status_filter=status_filter
        )

        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"清理任务失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': '清理任务失败',
            'message': str(e)
        }), 500
