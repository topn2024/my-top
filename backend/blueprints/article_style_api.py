#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文章风格转换 API
提供文章风格转换和批量转换接口
"""
from flask import Blueprint, request, jsonify
import logging
from logger_config import setup_logger, log_api_request

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ai_service_v2 import AIServiceV2
from services.platform_style_service import PlatformStyleService
from config import Config

logger = setup_logger(__name__)

# 创建蓝图
article_style_bp = Blueprint('article_style', __name__, url_prefix='/api/articles')


@article_style_bp.route('/convert-style', methods=['POST'])
def convert_article_style():
    """
    转换单篇文章风格

    Request Body:
        title: 原标题 (required)
        content: 原内容 (required)
        platform: 目标平台 (zhihu/csdn/juejin/xiaohongshu, required)
        platform_style_id: 平台风格ID (optional, 如果不提供则使用平台默认风格)
    """
    try:
        data = request.get_json()

        # 验证必填字段
        required_fields = ['title', 'content', 'platform']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        title = data['title']
        content = data['content']
        platform = data['platform']
        platform_style_id = data.get('platform_style_id')

        # 获取平台风格
        if platform_style_id:
            platform_style = PlatformStyleService.get_prompt(platform_style_id)
            if not platform_style:
                return jsonify({
                    'success': False,
                    'error': f'Platform style {platform_style_id} not found'
                }), 404
        else:
            # 使用平台默认风格
            platform_style = PlatformStyleService.get_default_style(
                platform=platform,
                apply_stage='publish'
            )
            if not platform_style:
                return jsonify({
                    'success': False,
                    'error': f'No default style found for platform: {platform}'
                }), 404

        # 初始化AI服务
        config = Config()
        ai_service = AIServiceV2(config)

        # 转换风格
        result = ai_service.convert_article_style(title, content, platform_style)

        # 增加使用次数
        PlatformStyleService.increment_usage(platform_style['id'])

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        logger.error(f'Failed to convert article style: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@article_style_bp.route('/batch-convert-style', methods=['POST'])
def batch_convert_articles():
    """
    批量转换文章风格

    Request Body:
        articles: 文章列表 [{title, content}, ...] (required)
        platform: 目标平台 (required)
        platform_style_id: 平台风格ID (optional)
    """
    try:
        data = request.get_json()

        if 'articles' not in data or not isinstance(data['articles'], list):
            return jsonify({
                'success': False,
                'error': 'Missing required field: articles (must be a list)'
            }), 400

        if 'platform' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: platform'
            }), 400

        articles = data['articles']
        platform = data['platform']
        platform_style_id = data.get('platform_style_id')

        # 验证文章列表
        for i, article in enumerate(articles):
            if 'title' not in article or 'content' not in article:
                return jsonify({
                    'success': False,
                    'error': f'Article {i} missing title or content'
                }), 400

        # 获取平台风格
        if platform_style_id:
            platform_style = PlatformStyleService.get_prompt(platform_style_id)
            if not platform_style:
                return jsonify({
                    'success': False,
                    'error': f'Platform style {platform_style_id} not found'
                }), 404
        else:
            platform_style = PlatformStyleService.get_default_style(
                platform=platform,
                apply_stage='publish'
            )
            if not platform_style:
                return jsonify({
                    'success': False,
                    'error': f'No default style found for platform: {platform}'
                }), 404

        # 初始化AI服务
        config = Config()
        ai_service = AIServiceV2(config)

        # 批量转换
        converted_articles = ai_service.batch_convert_styles(articles, platform_style)

        # 增加使用次数
        PlatformStyleService.increment_usage(platform_style['id'])

        return jsonify({
            'success': True,
            'data': {
                'converted_articles': converted_articles,
                'total': len(converted_articles),
                'platform_style_used': platform_style['name']
            }
        })

    except Exception as e:
        logger.error(f'Failed to batch convert articles: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@article_style_bp.route('/preview-style', methods=['POST'])
def preview_style_conversion():
    """
    预览风格转换效果（不保存）

    Request Body:
        title: 原标题
        content: 原内容（可以只提供部分内容作为预览）
        platform: 目标平台
        platform_style_id: 平台风格ID (optional)
    """
    try:
        data = request.get_json()

        required_fields = ['title', 'content', 'platform']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        title = data['title']
        content = data['content']
        platform = data['platform']
        platform_style_id = data.get('platform_style_id')

        # 获取平台风格
        if platform_style_id:
            platform_style = PlatformStyleService.get_prompt(platform_style_id)
        else:
            platform_style = PlatformStyleService.get_default_style(platform, 'publish')

        if not platform_style:
            return jsonify({
                'success': False,
                'error': 'Platform style not found'
            }), 404

        # 初始化AI服务
        config = Config()
        ai_service = AIServiceV2(config)

        # 转换风格（预览模式，不增加使用次数）
        result = ai_service.convert_article_style(title, content, platform_style)

        return jsonify({
            'success': True,
            'data': {
                'preview': result,
                'platform_style': {
                    'id': platform_style['id'],
                    'name': platform_style['name'],
                    'platform': platform_style['platform']
                }
            }
        })

    except Exception as e:
        logger.error(f'Failed to preview style conversion: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@article_style_bp.route('/compare-styles', methods=['POST'])
def compare_platform_styles():
    """
    比较不同平台风格的转换效果

    Request Body:
        title: 原标题 (required)
        content: 原内容 (required)
        platforms: 平台列表 (required, e.g., ['zhihu', 'csdn', 'juejin'])
    """
    try:
        data = request.get_json()

        required_fields = ['title', 'content', 'platforms']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        title = data['title']
        content = data['content']
        platforms = data['platforms']

        if not isinstance(platforms, list) or len(platforms) == 0:
            return jsonify({
                'success': False,
                'error': 'platforms must be a non-empty list'
            }), 400

        # 初始化AI服务
        config = Config()
        ai_service = AIServiceV2(config)

        # 为每个平台转换
        comparisons = []
        for platform in platforms:
            platform_style = PlatformStyleService.get_default_style(platform, 'publish')
            if platform_style:
                result = ai_service.convert_article_style(title, content, platform_style)
                comparisons.append({
                    'platform': platform,
                    'platform_style_name': platform_style['name'],
                    'converted': result
                })

        return jsonify({
            'success': True,
            'data': {
                'original': {'title': title, 'content': content},
                'comparisons': comparisons
            }
        })

    except Exception as e:
        logger.error(f'Failed to compare platform styles: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
