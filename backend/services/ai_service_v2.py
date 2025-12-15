#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI服务V2 - 支持三模块提示词系统
继承原有AIService，增加对analysis_prompts、article_prompts、platform_style_prompts的支持
"""
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger_config import setup_logger, log_service_call
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ai_service import AIService, remove_markdown_and_ai_traces

logger = setup_logger(__name__)


class AIServiceV2(AIService):
    """AI服务V2，支持三模块提示词系统"""


    @log_service_call("使用新提示词分析")
    def analyze_with_prompt(self, company_info: Dict, analysis_prompt: Dict) -> str:
        """
        使用分析提示词分析公司信息

        Args:
            company_info: 公司信息 {company_name, company_desc, uploaded_text}
            analysis_prompt: 分析提示词字典

        Returns:
            分析结果文本
        """
        # 渲染用户提示词模板
        user_prompt = self.render_prompt_template(
            analysis_prompt['user_template'],
            {
                'company_name': company_info.get('company_name', ''),
                'company_desc': company_info.get('company_desc', ''),
                'uploaded_text': company_info.get('uploaded_text', '')
            }
        )

        messages = [
            {'role': 'system', 'content': analysis_prompt['system_prompt']},
            {'role': 'user', 'content': user_prompt}
        ]

        logger.info(f"Using analysis prompt: {analysis_prompt['name']}")

        return self._call_api(
            messages,
            temperature=analysis_prompt.get('temperature', 0.7),
            max_tokens=analysis_prompt.get('max_tokens', 2000)
        )

    def generate_article_with_prompt(
        self,
        company_name: str,
        analysis: str,
        angle: str,
        article_prompt: Dict,
        platform_style: Optional[Dict] = None
    ) -> Dict:
        """
        使用文章提示词生成单篇文章（可选择在此阶段应用平台风格）

        Args:
            company_name: 公司名称
            analysis: 分析结果
            angle: 文章角度
            article_prompt: 文章提示词字典
            platform_style: 平台风格字典（可选，如果apply_stage='generation'）

        Returns:
            文章字典 {title, content, type}
        """
        # 渲染用户提示词
        user_prompt = self.render_prompt_template(
            article_prompt['user_template'],
            {
                'company_name': company_name,
                'analysis': analysis,
                'angle': angle
            }
        )

        # 基础系统提示词
        system_prompt = article_prompt['system_prompt']

        # 如果指定平台风格且在生成阶段应用
        if platform_style and platform_style.get('apply_stage') in ['generation', 'both']:
            system_prompt += f"\n\n{platform_style['system_prompt']}"
            logger.info(f"Applying platform style at generation: {platform_style['name']}")

        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ]

        logger.info(f"Generating article with prompt: {article_prompt['name']}, angle: {angle}")

        content = self._call_api(
            messages,
            temperature=article_prompt.get('temperature', 0.8),
            max_tokens=article_prompt.get('max_tokens', 3000)
        )

        # 解析标题和正文
        title, body = self._parse_article(content)

        # 清理markdown格式和AI痕迹
        if body:
            body = remove_markdown_and_ai_traces(body)

        return {
            'title': title or f'{company_name} - {angle}相关内容',
            'content': body or content,
            'type': angle
        }


    @log_service_call("使用新提示词生成文章")
    def generate_articles_with_prompts(
        self,
        company_name: str,
        analysis: str,
        article_prompt: Dict,
        article_count: int = 3,
        platform_style: Optional[Dict] = None
    ) -> List[Dict]:
        """
        使用文章提示词并发生成多篇文章

        Args:
            company_name: 公司名称
            analysis: 分析结果
            article_prompt: 文章提示词字典
            article_count: 文章数量
            platform_style: 平台风格（可选）

        Returns:
            文章列表
        """
        # 获取文章角度（优先使用提示词中定义的default_angles）
        angles = article_prompt.get('default_angles', [])
        if not angles:
            angles = ["技术创新", "行业应用", "用户价值", "市场趋势", "案例分析"]

        # 使用线程池并发生成文章
        articles = []
        with ThreadPoolExecutor(max_workers=min(article_count, 5)) as executor:
            future_to_index = {}
            for i in range(article_count):
                angle = angles[i % len(angles)]
                future = executor.submit(
                    self._generate_single_article_v2,
                    company_name, analysis, angle, i, article_count,
                    article_prompt, platform_style
                )
                future_to_index[future] = i

            # 收集结果
            for future in as_completed(future_to_index):
                article = future.result()
                if article:
                    articles.append(article)

        # 按索引排序
        articles.sort(key=lambda x: x.get('index', 0))

        # 移除索引字段
        for article in articles:
            article.pop('index', None)

        logger.info(f"Successfully generated {len(articles)}/{article_count} articles")
        return articles

    def _generate_single_article_v2(
        self,
        company_name: str,
        analysis: str,
        angle: str,
        index: int,
        total: int,
        article_prompt: Dict,
        platform_style: Optional[Dict] = None
    ) -> Dict:
        """生成单篇文章（V2版本，内部使用）"""
        try:
            article = self.generate_article_with_prompt(
                company_name, analysis, angle,
                article_prompt, platform_style
            )
            article['index'] = index
            logger.info(f"Article {index+1}/{total} ({angle}) generated successfully")
            return article
        except Exception as e:
            logger.error(f"Failed to generate article {index+1} ({angle}): {e}", exc_info=True)
            return None

    def convert_article_style(
        self,
        title: str,
        content: str,
        platform_style: Dict
    ) -> Dict:
        """
        转换文章风格（发布前应用平台风格）

        Args:
            title: 原标题
            content: 原内容
            platform_style: 平台风格字典

        Returns:
            转换后的文章 {title, content, original_title, original_content}
        """
        # 检查是否应该在此阶段应用
        if platform_style.get('apply_stage') not in ['publish', 'both']:
            logger.warning(f"Platform style {platform_style['name']} is not configured for publish stage")
            return {
                'title': title,
                'content': content,
                'original_title': title,
                'original_content': content,
                'converted': False
            }

        # 渲染用户提示词
        user_prompt = self.render_prompt_template(
            platform_style['user_template'],
            {
                'title': title,
                'content': content,
                'platform': platform_style['platform']
            }
        )

        messages = [
            {'role': 'system', 'content': platform_style['system_prompt']},
            {'role': 'user', 'content': user_prompt}
        ]

        logger.info(f"Converting article style to: {platform_style['name']}")

        response = self._call_api(
            messages,
            temperature=platform_style.get('temperature', 0.7),
            max_tokens=platform_style.get('max_tokens', 3000)
        )

        # 解析转换后的标题和正文
        new_title, new_content = self._parse_article(response)

        # 如果解析失败，使用原标题和响应内容
        if not new_title:
            new_title = title
        if not new_content:
            new_content = response

        return {
            'title': new_title,
            'content': new_content,
            'original_title': title,
            'original_content': content,
            'converted': True,
            'platform': platform_style['platform'],
            'platform_style_name': platform_style['name']
        }

    def batch_convert_styles(
        self,
        articles: List[Dict],
        platform_style: Dict
    ) -> List[Dict]:
        """
        批量转换文章风格

        Args:
            articles: 文章列表 [{title, content}, ...]
            platform_style: 平台风格字典

        Returns:
            转换后的文章列表
        """
        converted_articles = []

        with ThreadPoolExecutor(max_workers=min(len(articles), 5)) as executor:
            future_to_index = {}
            for i, article in enumerate(articles):
                future = executor.submit(
                    self.convert_article_style,
                    article['title'],
                    article['content'],
                    platform_style
                )
                future_to_index[future] = i

            # 收集结果
            results = [None] * len(articles)
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                result = future.result()
                if result:
                    results[index] = result

            # 过滤None值
            converted_articles = [r for r in results if r is not None]

        logger.info(f"Successfully converted {len(converted_articles)}/{len(articles)} articles")
        return converted_articles

    def analyze_and_generate_with_prompts(
        self,
        company_info: Dict,
        analysis_prompt: Dict,
        article_prompt: Dict,
        article_count: int = 3,
        platform_style: Optional[Dict] = None,
        apply_style_at_generation: bool = True
    ) -> Dict:
        """
        完整流程：分析 + 生成文章（可选平台风格）

        Args:
            company_info: 公司信息
            analysis_prompt: 分析提示词
            article_prompt: 文章提示词
            article_count: 文章数量
            platform_style: 平台风格（可选）
            apply_style_at_generation: 是否在生成阶段应用风格（否则返回原文章，由前端控制转换）

        Returns:
            {analysis, articles}
        """
        # 1. 分析
        analysis = self.analyze_with_prompt(company_info, analysis_prompt)

        # 2. 生成文章
        style_for_generation = None
        if platform_style and apply_style_at_generation:
            if platform_style.get('apply_stage') in ['generation', 'both']:
                style_for_generation = platform_style

        articles = self.generate_articles_with_prompts(
            company_info['company_name'],
            analysis,
            article_prompt,
            article_count,
            style_for_generation
        )

        return {
            'analysis': analysis,
            'articles': articles,
            'analysis_prompt_used': analysis_prompt['name'],
            'article_prompt_used': article_prompt['name'],
            'platform_style_used': platform_style['name'] if platform_style else None,
            'style_applied_at_generation': style_for_generation is not None
        }
