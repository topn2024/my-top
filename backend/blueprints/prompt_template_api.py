#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提示词模板API（旧版本 - 已废弃）

⚠️ DEPRECATED: 此模块已废弃，保留仅用于向后兼容。
新功能请使用三模块提示词系统：
- analysis_prompt_api.py - 分析提示词
- article_prompt_api.py - 文章提示词
- platform_style_api.py - 平台风格

提供模板管理和使用的HTTP接口
"""
from flask import Blueprint, jsonify, request, session as flask_session
from services.prompt_template_service import PromptTemplateService
from models_prompt_template import PromptExampleLibrary
from models import SessionLocal
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logger_config import setup_logger, log_api_request

logger = setup_logger(__name__)

bp = Blueprint('prompt_templates', __name__, url_prefix='/api/prompt-templates')


def get_current_user_id():
    """获取当前用户ID"""
    return flask_session.get('user_id', 1)  # 默认返回1，实际应从session获取


def require_admin():
    """检查管理员权限"""
    # 简化版：暂时不检查，后续可以添加权限验证
    return True


# ============ 模板查询接口 ============

@bp.route('/templates', methods=['GET'])
@log_api_request("查询提示词模板列表")
def list_templates():
    """
    列出所有模板
    Query params:
        - status: active/draft/archived
        - category_id: 分类ID
        - industry: 行业标签
        - platform: 平台标签
    """
    try:
        status = request.args.get('status')
        category_id = request.args.get('category_id', type=int)
        industry = request.args.get('industry')
        platform = request.args.get('platform')

        templates = PromptTemplateService.list_templates(
            status=status,
            category_id=category_id,
            industry=industry,
            platform=platform
        )

        return jsonify({
            'success': True,
            'data': templates,
            'count': len(templates)
        })

    except Exception as e:
        logger.error(f"Error listing templates: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/templates/<int:template_id>', methods=['GET'])
@log_api_request("获取提示词模板详情")
def get_template(template_id):
    """获取模板详情"""
    try:
        template = PromptTemplateService.get_template(template_id)

        if not template:
            return jsonify({'success': False, 'error': 'Template not found'}), 404

        return jsonify({'success': True, 'data': template})

    except Exception as e:
        logger.error(f"Error getting template: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/templates/by-code/<string:code>', methods=['GET'])
def get_template_by_code(code):
    """通过代码获取模板"""
    try:
        template = PromptTemplateService.get_template_by_code(code)

        if not template:
            return jsonify({'success': False, 'error': 'Template not found'}), 404

        return jsonify({'success': True, 'data': template})

    except Exception as e:
        logger.error(f"Error getting template by code: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ============ 模板管理接口（管理员）============

@bp.route('/admin/templates', methods=['POST'])
@log_api_request("创建提示词模板")
def create_template():
    """创建模板"""
    try:
        if not require_admin():
            return jsonify({'success': False, 'error': 'Permission denied'}), 403

        data = request.get_json()
        user_id = get_current_user_id()

        # 验证必填字段
        required_fields = ['name', 'code', 'prompts']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        template = PromptTemplateService.create_template(data, user_id)

        return jsonify({'success': True, 'data': template}), 201

    except Exception as e:
        logger.error(f"Error creating template: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/admin/templates/<int:template_id>', methods=['PUT'])
@log_api_request("更新提示词模板")
def update_template(template_id):
    """更新模板"""
    try:
        logger.info(f"→ 步骤1: 验证管理员权限")
        if not require_admin():
            logger.warning(f"✗ 权限验证失败: 非管理员用户尝试更新模板 ID={template_id}")
            return jsonify({'success': False, 'error': 'Permission denied'}), 403

        data = request.get_json()
        user_id = get_current_user_id()

        logger.info(f"→ 步骤2: 准备更新模板 ID={template_id}")
        logger.info(f"  - 操作用户: {user_id}")
        logger.info(f"  - 更新字段: {list(data.keys()) if data else []}")

        # 记录关键字段变更
        if 'name' in data:
            logger.info(f"  - 模板名称 → {data['name']}")
        if 'status' in data:
            logger.info(f"  - 状态变更 → {data['status']}")
        if 'analysis_system_prompt' in data or 'article_system_prompt' in data:
            logger.info(f"  - 提示词内容已更新")

        logger.info(f"→ 步骤3: 调用服务层更新模板")
        template = PromptTemplateService.update_template(template_id, data, user_id)

        logger.info(f"✓ 步骤4: 模板更新成功 ID={template_id}")

        return jsonify({'success': True, 'data': template})

    except ValueError as e:
        logger.error(f"✗ 模板不存在 ID={template_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 404
    except Exception as e:
        logger.error(f"✗ 更新模板失败 ID={template_id}: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/admin/templates/<int:template_id>', methods=['DELETE'])
@log_api_request("删除提示词模板")
def delete_template(template_id):
    """删除模板"""
    try:
        if not require_admin():
            return jsonify({'success': False, 'error': 'Permission denied'}), 403

        user_id = get_current_user_id()
        success = PromptTemplateService.delete_template(template_id, user_id)

        if not success:
            return jsonify({'success': False, 'error': 'Template not found'}), 404

        return jsonify({'success': True, 'message': 'Template deleted'})

    except Exception as e:
        logger.error(f"Error deleting template: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/admin/templates/<int:template_id>/activate', methods=['POST'])
def activate_template(template_id):
    """激活模板"""
    try:
        if not require_admin():
            return jsonify({'success': False, 'error': 'Permission denied'}), 403

        user_id = get_current_user_id()
        template = PromptTemplateService.activate_template(template_id, user_id)

        return jsonify({'success': True, 'data': template})

    except Exception as e:
        logger.error(f"Error activating template: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/admin/templates/<int:template_id>/archive', methods=['POST'])
def archive_template(template_id):
    """归档模板"""
    try:
        if not require_admin():
            return jsonify({'success': False, 'error': 'Permission denied'}), 403

        user_id = get_current_user_id()
        template = PromptTemplateService.archive_template(template_id, user_id)

        return jsonify({'success': True, 'data': template})

    except Exception as e:
        logger.error(f"Error archiving template: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ============ 分类接口 ============

@bp.route('/categories', methods=['GET'])
def list_categories():
    """列出所有分类"""
    try:
        categories = PromptTemplateService.list_categories()
        return jsonify({'success': True, 'data': categories})

    except Exception as e:
        logger.error(f"Error listing categories: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/categories/<int:category_id>', methods=['GET'])
def get_category(category_id):
    """获取分类详情"""
    try:
        category = PromptTemplateService.get_category(category_id)

        if not category:
            return jsonify({'success': False, 'error': 'Category not found'}), 404

        return jsonify({'success': True, 'data': category})

    except Exception as e:
        logger.error(f"Error getting category: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ============ 样例库接口 ============

@bp.route('/examples', methods=['GET'])
def list_examples():
    """
    列出样例库
    Query params:
        - type: industry_feature/platform_style/full_template/best_practice
        - industry: 行业
        - platform: 平台
    """
    try:
        example_type = request.args.get('type')
        industry = request.args.get('industry')
        platform = request.args.get('platform')

        session = SessionLocal()
        try:
            query = session.query(PromptExampleLibrary)

            if example_type:
                query = query.filter_by(type=example_type)
            if industry:
                query = query.filter_by(industry=industry)
            if platform:
                query = query.filter_by(platform=platform)

            examples = query.order_by(
                PromptExampleLibrary.display_order,
                PromptExampleLibrary.created_at.desc()
            ).all()

            return jsonify({
                'success': True,
                'data': [e.to_dict() for e in examples],
                'count': len(examples)
            })

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error listing examples: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/examples/<int:example_id>', methods=['GET'])
def get_example(example_id):
    """获取样例详情"""
    try:
        session = SessionLocal()
        try:
            example = session.query(PromptExampleLibrary).get(example_id)

            if not example:
                return jsonify({'success': False, 'error': 'Example not found'}), 404

            # 增加查看次数
            example.view_count += 1
            session.commit()

            return jsonify({'success': True, 'data': example.to_dict()})

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error getting example: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ============ 审计日志接口 ============

@bp.route('/admin/templates/<int:template_id>/audit-logs', methods=['GET'])
def get_audit_logs(template_id):
    """获取模板的审计日志"""
    try:
        if not require_admin():
            return jsonify({'success': False, 'error': 'Permission denied'}), 403

        limit = request.args.get('limit', 50, type=int)
        logs = PromptTemplateService.get_audit_logs(template_id, limit)

        return jsonify({'success': True, 'data': logs})

    except Exception as e:
        logger.error(f"Error getting audit logs: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ============ 统计接口 ============

@bp.route('/stats', methods=['GET'])
@log_api_request("获取模板统计信息")
def get_stats():
    """获取统计信息"""
    try:
        from models_prompt_template import PromptTemplate, PromptTemplateCategory, PromptTemplateUsageLog
        from datetime import datetime
        from sqlalchemy import func

        session = SessionLocal()
        try:
            total_templates = session.query(PromptTemplate).count()
            active_templates = session.query(PromptTemplate).filter_by(status='active').count()
            total_categories = session.query(PromptTemplateCategory).count()
            total_examples = session.query(PromptExampleLibrary).count()

            # 计算今日使用次数
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_usage = session.query(func.count(PromptTemplateUsageLog.id)).filter(
                PromptTemplateUsageLog.used_at >= today_start
            ).scalar() or 0

            # 计算总使用次数
            total_usage = session.query(func.sum(PromptTemplate.usage_count)).scalar() or 0

            return jsonify({
                'success': True,
                'data': {
                    'total_templates': total_templates,
                    'active_templates': active_templates,
                    'total_categories': total_categories,
                    'total_examples': total_examples,
                    'today_usage': today_usage,
                    'total_usage': total_usage
                }
            })

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
