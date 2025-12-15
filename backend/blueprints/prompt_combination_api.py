#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提示词组合推荐 API
提供智能推荐和组合管理接口
"""
from flask import Blueprint, request, jsonify
import logging
from logger_config import setup_logger, log_api_request

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.prompt_combination_service import PromptCombinationService

logger = setup_logger(__name__)

# 创建蓝图
combination_bp = Blueprint('prompt_combination', __name__, url_prefix='/api/prompts/combinations')


@combination_bp.route('/recommend', methods=['POST'])
def get_recommendation():
    """
    智能推荐提示词组合

    Request Body:
        company_info: 公司信息 {company_name, company_desc}
        target_platform: 目标平台 (zhihu/csdn/juejin/xiaohongshu, optional)
        user_id: 用户ID (optional)
    """
    try:
        data = request.get_json()

        if 'company_info' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: company_info'
            }), 400

        company_info = data['company_info']
        target_platform = data.get('target_platform')
        user_id = data.get('user_id') or request.headers.get('X-User-ID')

        recommendation = PromptCombinationService.get_recommended_combination(
            company_info=company_info,
            target_platform=target_platform,
            user_id=user_id
        )

        return jsonify({
            'success': True,
            'data': recommendation
        })

    except Exception as e:
        logger.error(f'Failed to get recommendation: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@combination_bp.route('/available', methods=['GET'])
def get_available_combinations():
    """
    获取可用的提示词组合列表

    Query Parameters:
        industry: 行业筛选
        platform: 平台筛选
    """
    try:
        industry = request.args.get('industry')
        platform = request.args.get('platform')

        combinations = PromptCombinationService.get_available_combinations(
            industry=industry,
            platform=platform
        )

        return jsonify({
            'success': True,
            'data': combinations
        })

    except Exception as e:
        logger.error(f'Failed to get available combinations: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@combination_bp.route('/log', methods=['POST'])
def log_usage():
    """
    记录提示词组合使用

    Request Body:
        user_id: 用户ID (required)
        workflow_id: 工作流ID (optional)
        analysis_prompt_id: 分析提示词ID (optional)
        article_prompt_id: 文章提示词ID (optional)
        platform_style_prompt_id: 平台风格提示词ID (optional)
        selection_method: 选择方式 (manual/auto/recommended, default: manual)
        applied_at_generation: 是否在生成阶段应用 (boolean, default: false)
        applied_at_publish: 是否在发布阶段应用 (boolean, default: false)
    """
    try:
        data = request.get_json()

        user_id = data.get('user_id') or request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'Missing required field: user_id'
            }), 400

        log_id = PromptCombinationService.log_combination_usage(
            user_id=user_id,
            workflow_id=data.get('workflow_id'),
            analysis_prompt_id=data.get('analysis_prompt_id'),
            article_prompt_id=data.get('article_prompt_id'),
            platform_style_prompt_id=data.get('platform_style_prompt_id'),
            selection_method=data.get('selection_method', 'manual'),
            applied_at_generation=data.get('applied_at_generation', False),
            applied_at_publish=data.get('applied_at_publish', False)
        )

        return jsonify({
            'success': True,
            'data': {'log_id': log_id}
        }), 201

    except Exception as e:
        logger.error(f'Failed to log combination usage: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@combination_bp.route('/log/<int:log_id>/result', methods=['PUT'])
def update_log_result(log_id):
    """
    更新组合使用结果

    Request Body:
        status: 状态 (success/failed/partial, required)
        articles_generated: 生成的文章数 (optional)
        articles_published: 发布的文章数 (optional)
        error_message: 错误信息 (optional)
    """
    try:
        data = request.get_json()

        if 'status' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: status'
            }), 400

        success = PromptCombinationService.update_log_result(
            log_id=log_id,
            status=data['status'],
            articles_generated=data.get('articles_generated', 0),
            articles_published=data.get('articles_published', 0),
            error_message=data.get('error_message')
        )

        if not success:
            return jsonify({
                'success': False,
                'error': 'Log not found'
            }), 404

        return jsonify({
            'success': True,
            'message': 'Log result updated'
        })

    except Exception as e:
        logger.error(f'Failed to update log result {log_id}: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@combination_bp.route('/history', methods=['GET'])
def get_user_history():
    """
    获取用户的组合使用历史

    Query Parameters:
        user_id: 用户ID (required if not in header)
        page: 页码 (default: 1)
        page_size: 每页大小 (default: 20)
    """
    try:
        user_id = request.args.get('user_id') or request.headers.get('X-User-ID')

        if not user_id:
            return jsonify({
                'success': False,
                'error': 'Missing required parameter: user_id'
            }), 400

        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))

        history = PromptCombinationService.get_user_combination_history(
            user_id=int(user_id),
            page=page,
            page_size=page_size
        )

        return jsonify({
            'success': True,
            'data': history
        })

    except Exception as e:
        logger.error(f'Failed to get user combination history: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
