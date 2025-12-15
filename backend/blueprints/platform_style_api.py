#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
平台风格提示词 API
提供平台风格提示词的REST接口
"""
from flask import Blueprint, request, jsonify
import logging
from logger_config import setup_logger, log_api_request

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.platform_style_service import PlatformStyleService

logger = setup_logger(__name__)

# 创建蓝图
platform_style_bp = Blueprint('platform_style', __name__, url_prefix='/api/prompts/platform-style')


@platform_style_bp.route('', methods=['GET'])
def list_prompts():
    """
    列出平台风格提示词

    Query Parameters:
        platform: 平台筛选 (zhihu/csdn/juejin/xiaohongshu)
        status: 状态筛选
        apply_stage: 应用阶段筛选 (generation/publish/both)
        search: 搜索关键词
        page: 页码
        page_size: 每页大小
    """
    try:
        platform = request.args.get('platform')
        status = request.args.get('status')
        apply_stage = request.args.get('apply_stage')
        search_keyword = request.args.get('search')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))

        result = PlatformStyleService.list_prompts(
            platform=platform,
            status=status,
            apply_stage=apply_stage,
            search_keyword=search_keyword,
            page=page,
            page_size=page_size
        )

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        logger.error(f'Failed to list platform style prompts: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@platform_style_bp.route('/<int:prompt_id>', methods=['GET'])
def get_prompt(prompt_id):
    """获取单个平台风格提示词详情"""
    try:
        prompt = PlatformStyleService.get_prompt(prompt_id)

        if not prompt:
            return jsonify({
                'success': False,
                'error': 'Prompt not found'
            }), 404

        return jsonify({
            'success': True,
            'data': prompt
        })

    except Exception as e:
        logger.error(f'Failed to get platform style prompt {prompt_id}: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@platform_style_bp.route('/code/<code>', methods=['GET'])
def get_prompt_by_code(code):
    """根据代码获取平台风格提示词"""
    try:
        prompt = PlatformStyleService.get_prompt_by_code(code)

        if not prompt:
            return jsonify({
                'success': False,
                'error': 'Prompt not found'
            }), 404

        return jsonify({
            'success': True,
            'data': prompt
        })

    except Exception as e:
        logger.error(f'Failed to get platform style prompt by code {code}: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@platform_style_bp.route('/by-platform/<platform>', methods=['GET'])
def get_styles_by_platform(platform):
    """
    根据平台获取所有风格提示词

    Query Parameters:
        apply_stage: 应用阶段筛选 (generation/publish/both)
    """
    try:
        apply_stage = request.args.get('apply_stage')

        styles = PlatformStyleService.get_styles_by_platform(
            platform=platform,
            apply_stage=apply_stage
        )

        return jsonify({
            'success': True,
            'data': styles
        })

    except Exception as e:
        logger.error(f'Failed to get styles for platform {platform}: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@platform_style_bp.route('/default/<platform>', methods=['GET'])
def get_default_style(platform):
    """
    获取平台的默认风格

    Query Parameters:
        apply_stage: 应用阶段筛选
    """
    try:
        apply_stage = request.args.get('apply_stage')

        style = PlatformStyleService.get_default_style(
            platform=platform,
            apply_stage=apply_stage
        )

        if not style:
            return jsonify({
                'success': False,
                'error': f'No default style found for platform: {platform}'
            }), 404

        return jsonify({
            'success': True,
            'data': style
        })

    except Exception as e:
        logger.error(f'Failed to get default style for platform {platform}: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@platform_style_bp.route('', methods=['POST'])
def create_prompt():
    """
    创建新的平台风格提示词

    Request Body:
        name: 名称 (required)
        code: 代码 (required)
        platform: 平台 (required, zhihu/csdn/juejin/xiaohongshu)
        system_prompt: 系统提示词 (required)
        user_template: 用户模板 (required)
        style_features: 风格特征
        apply_stage: 应用阶段 (generation/publish/both)
        ...
    """
    try:
        data = request.get_json()

        required_fields = ['name', 'code', 'platform', 'system_prompt', 'user_template']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        # 验证平台值
        if data['platform'] not in PlatformStyleService.SUPPORTED_PLATFORMS:
            return jsonify({
                'success': False,
                'error': f'Invalid platform. Must be one of: {", ".join(PlatformStyleService.SUPPORTED_PLATFORMS)}'
            }), 400

        user_id = request.headers.get('X-User-ID')
        prompt = PlatformStyleService.create_prompt(data, created_by=user_id)

        return jsonify({
            'success': True,
            'data': prompt
        }), 201

    except Exception as e:
        logger.error(f'Failed to create platform style prompt: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@platform_style_bp.route('/<int:prompt_id>', methods=['PUT'])
def update_prompt(prompt_id):
    """更新平台风格提示词"""
    try:
        data = request.get_json()
        user_id = request.headers.get('X-User-ID')

        # 如果更新platform字段，验证值
        if 'platform' in data and data['platform'] not in PlatformStyleService.SUPPORTED_PLATFORMS:
            return jsonify({
                'success': False,
                'error': f'Invalid platform. Must be one of: {", ".join(PlatformStyleService.SUPPORTED_PLATFORMS)}'
            }), 400

        prompt = PlatformStyleService.update_prompt(prompt_id, data, updated_by=user_id)

        if not prompt:
            return jsonify({
                'success': False,
                'error': 'Prompt not found'
            }), 404

        return jsonify({
            'success': True,
            'data': prompt
        })

    except Exception as e:
        logger.error(f'Failed to update platform style prompt {prompt_id}: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@platform_style_bp.route('/<int:prompt_id>', methods=['DELETE'])
def delete_prompt(prompt_id):
    """删除平台风格提示词（软删除）"""
    try:
        success = PlatformStyleService.delete_prompt(prompt_id)

        if not success:
            return jsonify({
                'success': False,
                'error': 'Prompt not found'
            }), 404

        return jsonify({
            'success': True,
            'message': 'Prompt archived successfully'
        })

    except Exception as e:
        logger.error(f'Failed to delete platform style prompt {prompt_id}: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@platform_style_bp.route('/<int:prompt_id>/increment-usage', methods=['POST'])
def increment_usage(prompt_id):
    """增加使用次数"""
    try:
        success = PlatformStyleService.increment_usage(prompt_id)

        if not success:
            return jsonify({
                'success': False,
                'error': 'Failed to increment usage'
            }), 500

        return jsonify({
            'success': True,
            'message': 'Usage incremented'
        })

    except Exception as e:
        logger.error(f'Failed to increment usage for prompt {prompt_id}: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@platform_style_bp.route('/<int:prompt_id>/update-statistics', methods=['POST'])
def update_statistics(prompt_id):
    """
    更新统计信息

    Request Body:
        success: 是否成功 (boolean)
        rating: 用户评分 (1-5)
    """
    try:
        data = request.get_json()

        if 'success' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: success'
            }), 400

        success = PlatformStyleService.update_statistics(
            prompt_id,
            success=data['success'],
            rating=data.get('rating')
        )

        if not success:
            return jsonify({
                'success': False,
                'error': 'Prompt not found'
            }), 404

        return jsonify({
            'success': True,
            'message': 'Statistics updated'
        })

    except Exception as e:
        logger.error(f'Failed to update statistics for prompt {prompt_id}: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@platform_style_bp.route('/platforms', methods=['GET'])
def get_all_platforms():
    """获取所有支持的平台及其默认风格"""
    try:
        platforms = PlatformStyleService.get_all_platforms()

        return jsonify({
            'success': True,
            'data': platforms
        })

    except Exception as e:
        logger.error(f'Failed to get platforms: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
