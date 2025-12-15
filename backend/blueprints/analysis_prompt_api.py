#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析提示词 API
提供分析提示词的REST接口
"""
from flask import Blueprint, request, jsonify
import logging
from logger_config import setup_logger, log_api_request

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.analysis_prompt_service import AnalysisPromptService

logger = setup_logger(__name__)

# 创建蓝图
analysis_prompt_bp = Blueprint('analysis_prompt', __name__, url_prefix='/api/prompts/analysis')


@log_api_request("查询分析提示词列表")
@log_api_request("查询分析提示词列表")
@analysis_prompt_bp.route('', methods=['GET'])
def list_prompts():
    """
    列出分析提示词

    Query Parameters:
        status: 状态筛选 (draft/active/archived)
        industry_tag: 行业标签筛选
        search: 搜索关键词
        page: 页码 (默认1)
        page_size: 每页大小 (默认20)
    """
    try:
        status = request.args.get('status')
        industry_tag = request.args.get('industry_tag')
        search_keyword = request.args.get('search')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))

        result = AnalysisPromptService.list_prompts(
            status=status,
            industry_tag=industry_tag,
            search_keyword=search_keyword,
            page=page,
            page_size=page_size
        )

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        logger.error(f'Failed to list analysis prompts: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@log_api_request("获取分析提示词详情")
@log_api_request("获取分析提示词详情")
@analysis_prompt_bp.route('/<int:prompt_id>', methods=['GET'])
def get_prompt(prompt_id):
    """获取单个分析提示词详情"""
    try:
        prompt = AnalysisPromptService.get_prompt(prompt_id)

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
        logger.error(f'Failed to get analysis prompt {prompt_id}: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@analysis_prompt_bp.route('/code/<code>', methods=['GET'])
def get_prompt_by_code(code):
    """根据代码获取分析提示词"""
    try:
        prompt = AnalysisPromptService.get_prompt_by_code(code)

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
        logger.error(f'Failed to get analysis prompt by code {code}: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@analysis_prompt_bp.route('/default', methods=['GET'])
def get_default_prompt():
    """
    获取默认分析提示词

    Query Parameters:
        industry_tag: 行业标签（可选）
    """
    try:
        industry_tag = request.args.get('industry_tag')
        prompt = AnalysisPromptService.get_default_prompt(industry_tag=industry_tag)

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
        logger.error(f'Failed to get default analysis prompt: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@log_api_request("创建分析提示词")
@log_api_request("创建分析提示词")
@analysis_prompt_bp.route('', methods=['POST'])
def create_prompt():
    """
    创建新的分析提示词

    Request Body:
        name: 名称 (required)
        code: 代码 (required)
        description: 描述
        system_prompt: 系统提示词 (required)
        user_template: 用户模板 (required)
        variables: 变量列表
        temperature: 温度参数
        max_tokens: 最大token数
        industry_tags: 行业标签
        status: 状态
        is_default: 是否默认
        ...
    """
    try:
        data = request.get_json()

        # 验证必填字段
        required_fields = ['name', 'code', 'system_prompt', 'user_template']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        # 获取用户ID（从session或token）
        user_id = request.headers.get('X-User-ID')  # 简化版，实际应从认证系统获取

        prompt = AnalysisPromptService.create_prompt(data, created_by=user_id)

        return jsonify({
            'success': True,
            'data': prompt
        }), 201

    except Exception as e:
        logger.error(f'Failed to create analysis prompt: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@log_api_request("更新分析提示词")
@log_api_request("更新分析提示词")
@analysis_prompt_bp.route('/<int:prompt_id>', methods=['PUT'])
def update_prompt(prompt_id):
    """更新分析提示词"""
    try:
        data = request.get_json()
        user_id = request.headers.get('X-User-ID')

        prompt = AnalysisPromptService.update_prompt(prompt_id, data, updated_by=user_id)

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
        logger.error(f'Failed to update analysis prompt {prompt_id}: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@log_api_request("删除分析提示词")
@log_api_request("删除分析提示词")
@analysis_prompt_bp.route('/<int:prompt_id>', methods=['DELETE'])
def delete_prompt(prompt_id):
    """删除分析提示词（软删除）"""
    try:
        success = AnalysisPromptService.delete_prompt(prompt_id)

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
        logger.error(f'Failed to delete analysis prompt {prompt_id}: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@analysis_prompt_bp.route('/<int:prompt_id>/increment-usage', methods=['POST'])
def increment_usage(prompt_id):
    """增加使用次数"""
    try:
        success = AnalysisPromptService.increment_usage(prompt_id)

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


@analysis_prompt_bp.route('/<int:prompt_id>/update-statistics', methods=['POST'])
def update_statistics(prompt_id):
    """
    更新统计信息

    Request Body:
        success: 是否成功 (boolean, required)
        rating: 用户评分 (1-5, optional)
    """
    try:
        data = request.get_json()

        if 'success' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: success'
            }), 400

        success = AnalysisPromptService.update_statistics(
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


@analysis_prompt_bp.route('/industry-tags', methods=['GET'])
def get_industry_tags():
    """获取所有可用的行业标签"""
    try:
        tags = AnalysisPromptService.get_available_industry_tags()

        return jsonify({
            'success': True,
            'data': tags
        })

    except Exception as e:
        logger.error(f'Failed to get industry tags: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
