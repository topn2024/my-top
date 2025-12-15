#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文章提示词 API
提供文章生成提示词的REST接口
"""
from flask import Blueprint, request, jsonify
import logging
from logger_config import setup_logger, log_api_request

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.article_prompt_service import ArticlePromptService

logger = setup_logger(__name__)

# 创建蓝图
article_prompt_bp = Blueprint('article_prompt', __name__, url_prefix='/api/prompts/article')


@log_api_request("查询文章提示词列表")
@article_prompt_bp.route('', methods=['GET'])
def list_prompts():
    """
    列出文章生成提示词

    Query Parameters:
        status: 状态筛选
        industry_tag: 行业标签筛选
        style_tag: 风格标签筛选
        search: 搜索关键词
        page: 页码
        page_size: 每页大小
    """
    try:
        status = request.args.get('status')
        industry_tag = request.args.get('industry_tag')
        style_tag = request.args.get('style_tag')
        search_keyword = request.args.get('search')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))

        result = ArticlePromptService.list_prompts(
            status=status,
            industry_tag=industry_tag,
            style_tag=style_tag,
            search_keyword=search_keyword,
            page=page,
            page_size=page_size
        )

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        logger.error(f'Failed to list article prompts: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@log_api_request("获取文章提示词详情")
@article_prompt_bp.route('/<int:prompt_id>', methods=['GET'])
def get_prompt(prompt_id):
    """获取单个文章提示词详情"""
    try:
        prompt = ArticlePromptService.get_prompt(prompt_id)

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
        logger.error(f'Failed to get article prompt {prompt_id}: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@article_prompt_bp.route('/code/<code>', methods=['GET'])
def get_prompt_by_code(code):
    """根据代码获取文章提示词"""
    try:
        prompt = ArticlePromptService.get_prompt_by_code(code)

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
        logger.error(f'Failed to get article prompt by code {code}: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@article_prompt_bp.route('/default', methods=['GET'])
def get_default_prompt():
    """
    获取默认文章提示词

    Query Parameters:
        industry_tag: 行业标签
        style_tag: 风格标签
    """
    try:
        industry_tag = request.args.get('industry_tag')
        style_tag = request.args.get('style_tag')

        prompt = ArticlePromptService.get_default_prompt(
            industry_tag=industry_tag,
            style_tag=style_tag
        )

        if not prompt:
            return jsonify({
                'success': False,
                'error': 'No default prompt found'
            }), 404

        return jsonify({
            'success': True,
            'data': prompt
        })

    except Exception as e:
        logger.error(f'Failed to get default article prompt: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@log_api_request("创建文章提示词")
@article_prompt_bp.route('', methods=['POST'])
def create_prompt():
    """
    创建新的文章提示词

    Request Body:
        name: 名称 (required)
        code: 代码 (required)
        system_prompt: 系统提示词 (required)
        user_template: 用户模板 (required)
        default_angles: 默认文章角度列表
        ...
    """
    try:
        data = request.get_json()

        required_fields = ['name', 'code', 'system_prompt', 'user_template']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        user_id = request.headers.get('X-User-ID')
        prompt = ArticlePromptService.create_prompt(data, created_by=user_id)

        return jsonify({
            'success': True,
            'data': prompt
        }), 201

    except Exception as e:
        logger.error(f'Failed to create article prompt: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@log_api_request("更新文章提示词")
@article_prompt_bp.route('/<int:prompt_id>', methods=['PUT'])
def update_prompt(prompt_id):
    """更新文章提示词"""
    try:
        data = request.get_json()
        user_id = request.headers.get('X-User-ID')

        prompt = ArticlePromptService.update_prompt(prompt_id, data, updated_by=user_id)

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
        logger.error(f'Failed to update article prompt {prompt_id}: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@log_api_request("删除文章提示词")
@article_prompt_bp.route('/<int:prompt_id>', methods=['DELETE'])
def delete_prompt(prompt_id):
    """删除文章提示词（软删除）"""
    try:
        success = ArticlePromptService.delete_prompt(prompt_id)

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
        logger.error(f'Failed to delete article prompt {prompt_id}: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@article_prompt_bp.route('/<int:prompt_id>/increment-usage', methods=['POST'])
def increment_usage(prompt_id):
    """增加使用次数"""
    try:
        success = ArticlePromptService.increment_usage(prompt_id)

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


@article_prompt_bp.route('/<int:prompt_id>/update-statistics', methods=['POST'])
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

        success = ArticlePromptService.update_statistics(
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


@article_prompt_bp.route('/tags', methods=['GET'])
def get_tags():
    """获取所有可用的标签（行业标签和风格标签）"""
    try:
        tags = ArticlePromptService.get_available_tags()

        return jsonify({
            'success': True,
            'data': tags
        })

    except Exception as e:
        logger.error(f'Failed to get tags: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
