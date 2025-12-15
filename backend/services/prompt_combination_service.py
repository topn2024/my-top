#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提示词组合推荐服务
提供智能推荐和组合验证逻辑
"""
import json
import re
from typing import Dict, List, Optional
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import SessionLocal
from models_prompt_v2 import PromptCombinationLog
from services.analysis_prompt_service import AnalysisPromptService
from services.article_prompt_service import ArticlePromptService
from services.platform_style_service import PlatformStyleService


class PromptCombinationService:
    """提示词组合推荐服务类"""

    # 行业关键词映射
    INDUSTRY_KEYWORDS = {
        'tech': ['技术', '科技', 'AI', '人工智能', '软件', '互联网', 'SaaS', '云计算', '大数据'],
        'ai': ['AI', '人工智能', '机器学习', '深度学习', '算法', '模型'],
        'saas': ['SaaS', '云服务', '企业服务', '协作', '管理系统'],
        'ecommerce': ['电商', '电子商务', '购物', '零售', '商城'],
        'education': ['教育', '培训', '学习', '课程', '知识'],
        'finance': ['金融', '支付', '理财', '投资', '保险'],
        'healthcare': ['医疗', '健康', '医院', '诊断', '治疗'],
        'general': ['企业', '公司', '商业', '服务']
    }

    @staticmethod
    def detect_industry(company_desc: str) -> List[str]:
        """
        从公司描述中检测行业标签

        Args:
            company_desc: 公司描述文本

        Returns:
            检测到的行业标签列表
        """
        detected_industries = []

        for industry, keywords in PromptCombinationService.INDUSTRY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in company_desc:
                    detected_industries.append(industry)
                    break

        # 如果没有检测到具体行业，返回通用
        if not detected_industries:
            detected_industries.append('general')

        return detected_industries

    @staticmethod
    def get_recommended_combination(
        company_info: Dict,
        target_platform: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Dict:
        """
        智能推荐提示词组合

        Args:
            company_info: 公司信息 {company_name, company_desc, ...}
            target_platform: 目标平台 (zhihu/csdn/juejin/xiaohongshu)
            user_id: 用户ID（用于个性化推荐）

        Returns:
            推荐组合字典
        """
        # 1. 检测行业
        company_desc = company_info.get('company_desc', '')
        industries = PromptCombinationService.detect_industry(company_desc)
        primary_industry = industries[0] if industries else 'general'

        # 2. 获取用户历史偏好（如果有用户ID）
        user_preferences = None
        if user_id:
            user_preferences = PromptCombinationService._get_user_preferences(user_id)

        # 3. 推荐分析提示词
        analysis_prompt = PromptCombinationService._recommend_analysis_prompt(
            primary_industry,
            user_preferences
        )

        # 4. 推荐文章提示词
        article_prompt = PromptCombinationService._recommend_article_prompt(
            primary_industry,
            user_preferences
        )

        # 5. 推荐平台风格（如果指定平台）
        platform_style = None
        if target_platform:
            platform_style = PlatformStyleService.get_default_style(
                target_platform,
                apply_stage='both'
            )

        # 6. 生成推荐理由
        reason = PromptCombinationService._generate_recommendation_reason(
            primary_industry,
            target_platform,
            analysis_prompt,
            article_prompt,
            platform_style
        )

        return {
            'analysis_prompt': analysis_prompt,
            'article_prompt': article_prompt,
            'platform_style': platform_style,
            'detected_industries': industries,
            'primary_industry': primary_industry,
            'target_platform': target_platform,
            'reason': reason,
            'confidence': 0.85  # 推荐置信度（可基于更复杂的算法计算）
        }

    @staticmethod
    def _recommend_analysis_prompt(
        industry: str,
        user_preferences: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        推荐分析提示词

        Args:
            industry: 行业标签
            user_preferences: 用户偏好

        Returns:
            推荐的分析提示词
        """
        # 如果用户有偏好的分析提示词，优先使用
        if user_preferences and user_preferences.get('preferred_analysis_prompt_id'):
            prompt = AnalysisPromptService.get_prompt(
                user_preferences['preferred_analysis_prompt_id']
            )
            if prompt and prompt['status'] == 'active':
                return prompt

        # 否则根据行业获取默认提示词
        prompt = AnalysisPromptService.get_default_prompt(industry_tag=industry)

        # 如果没有找到，获取任意默认提示词
        if not prompt:
            prompt = AnalysisPromptService.get_default_prompt()

        return prompt

    @staticmethod
    def _recommend_article_prompt(
        industry: str,
        user_preferences: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        推荐文章提示词

        Args:
            industry: 行业标签
            user_preferences: 用户偏好

        Returns:
            推荐的文章提示词
        """
        # 用户偏好优先
        if user_preferences and user_preferences.get('preferred_article_prompt_id'):
            prompt = ArticlePromptService.get_prompt(
                user_preferences['preferred_article_prompt_id']
            )
            if prompt and prompt['status'] == 'active':
                return prompt

        # 根据行业获取默认提示词
        prompt = ArticlePromptService.get_default_prompt(industry_tag=industry)

        # 如果没有找到，获取任意默认提示词
        if not prompt:
            prompt = ArticlePromptService.get_default_prompt()

        return prompt

    @staticmethod
    def _get_user_preferences(user_id: int) -> Optional[Dict]:
        """
        获取用户的提示词使用偏好（基于历史记录）

        Args:
            user_id: 用户ID

        Returns:
            用户偏好字典或None
        """
        session = SessionLocal()
        try:
            # 查询最近成功的组合记录
            recent_logs = session.query(PromptCombinationLog).filter(
                PromptCombinationLog.user_id == user_id,
                PromptCombinationLog.status == 'success'
            ).order_by(
                PromptCombinationLog.created_at.desc()
            ).limit(10).all()

            if not recent_logs:
                return None

            # 统计最常用的提示词ID
            analysis_counts = {}
            article_counts = {}

            for log in recent_logs:
                if log.analysis_prompt_id:
                    analysis_counts[log.analysis_prompt_id] = analysis_counts.get(log.analysis_prompt_id, 0) + 1
                if log.article_prompt_id:
                    article_counts[log.article_prompt_id] = article_counts.get(log.article_prompt_id, 0) + 1

            # 获取最常用的ID
            preferred_analysis = max(analysis_counts, key=analysis_counts.get) if analysis_counts else None
            preferred_article = max(article_counts, key=article_counts.get) if article_counts else None

            return {
                'preferred_analysis_prompt_id': preferred_analysis,
                'preferred_article_prompt_id': preferred_article
            }
        finally:
            session.close()

    @staticmethod
    def _generate_recommendation_reason(
        industry: str,
        platform: Optional[str],
        analysis_prompt: Optional[Dict],
        article_prompt: Optional[Dict],
        platform_style: Optional[Dict]
    ) -> str:
        """
        生成推荐理由说明

        Args:
            industry: 检测到的行业
            platform: 目标平台
            analysis_prompt: 推荐的分析提示词
            article_prompt: 推荐的文章提示词
            platform_style: 推荐的平台风格

        Returns:
            推荐理由文本
        """
        industry_names = {
            'tech': '科技行业',
            'ai': 'AI行业',
            'saas': 'SaaS行业',
            'ecommerce': '电商行业',
            'education': '教育行业',
            'finance': '金融行业',
            'healthcare': '医疗行业',
            'general': '通用行业'
        }

        platform_names = {
            'zhihu': '知乎',
            'csdn': 'CSDN',
            'juejin': '掘金',
            'xiaohongshu': '小红书'
        }

        reason_parts = []

        # 行业匹配
        industry_name = industry_names.get(industry, industry)
        reason_parts.append(f"基于{industry_name}特征")

        # 分析提示词
        if analysis_prompt:
            reason_parts.append(f"推荐使用「{analysis_prompt['name']}」进行分析")

        # 文章提示词
        if article_prompt:
            reason_parts.append(f"使用「{article_prompt['name']}」生成文章")

        # 平台风格
        if platform_style and platform:
            platform_name = platform_names.get(platform, platform)
            reason_parts.append(f"针对{platform_name}平台优化")

        return "，".join(reason_parts) + "。"

    @staticmethod
    def get_available_combinations(
        industry: Optional[str] = None,
        platform: Optional[str] = None
    ) -> List[Dict]:
        """
        获取可用的提示词组合列表

        Args:
            industry: 行业筛选
            platform: 平台筛选

        Returns:
            组合列表
        """
        combinations = []

        # 获取活跃的分析提示词
        analysis_prompts = AnalysisPromptService.list_prompts(
            status='active',
            industry_tag=industry,
            page_size=100
        )['prompts']

        # 获取活跃的文章提示词
        article_prompts = ArticlePromptService.list_prompts(
            status='active',
            industry_tag=industry,
            page_size=100
        )['prompts']

        # 获取平台风格
        platform_styles = []
        if platform:
            platform_styles = PlatformStyleService.get_styles_by_platform(platform)
        else:
            # 获取所有平台的默认风格
            for p in PlatformStyleService.SUPPORTED_PLATFORMS:
                default = PlatformStyleService.get_default_style(p)
                if default:
                    platform_styles.append(default)

        # 生成组合
        for analysis in analysis_prompts[:5]:  # 限制组合数量
            for article in article_prompts[:3]:
                for style in platform_styles[:2]:
                    combinations.append({
                        'analysis_prompt_id': analysis['id'],
                        'analysis_prompt_name': analysis['name'],
                        'article_prompt_id': article['id'],
                        'article_prompt_name': article['name'],
                        'platform_style_id': style['id'],
                        'platform_style_name': style['name'],
                        'platform': style['platform']
                    })

        return combinations[:20]  # 返回前20个组合

    @staticmethod
    def log_combination_usage(
        user_id: int,
        workflow_id: Optional[int],
        analysis_prompt_id: Optional[int],
        article_prompt_id: Optional[int],
        platform_style_prompt_id: Optional[int],
        selection_method: str = 'manual',
        applied_at_generation: bool = False,
        applied_at_publish: bool = False
    ) -> int:
        """
        记录提示词组合使用

        Args:
            user_id: 用户ID
            workflow_id: 工作流ID
            analysis_prompt_id: 分析提示词ID
            article_prompt_id: 文章提示词ID
            platform_style_prompt_id: 平台风格提示词ID
            selection_method: 选择方式 (manual/auto/recommended)
            applied_at_generation: 是否在生成阶段应用
            applied_at_publish: 是否在发布阶段应用

        Returns:
            日志记录ID
        """
        session = SessionLocal()
        try:
            log = PromptCombinationLog(
                user_id=user_id,
                workflow_id=workflow_id,
                analysis_prompt_id=analysis_prompt_id,
                article_prompt_id=article_prompt_id,
                platform_style_prompt_id=platform_style_prompt_id,
                selection_method=selection_method,
                applied_at_generation=applied_at_generation,
                applied_at_publish=applied_at_publish,
                status='pending'
            )

            session.add(log)
            session.commit()
            session.refresh(log)

            return log.id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @staticmethod
    def update_log_result(
        log_id: int,
        status: str,
        articles_generated: int = 0,
        articles_published: int = 0,
        error_message: Optional[str] = None
    ) -> bool:
        """
        更新组合使用结果

        Args:
            log_id: 日志记录ID
            status: 状态 (success/failed/partial)
            articles_generated: 生成的文章数
            articles_published: 发布的文章数
            error_message: 错误信息

        Returns:
            是否成功
        """
        session = SessionLocal()
        try:
            log = session.query(PromptCombinationLog).filter(
                PromptCombinationLog.id == log_id
            ).first()

            if not log:
                return False

            log.status = status
            log.articles_generated = articles_generated
            log.articles_published = articles_published
            log.error_message = error_message

            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @staticmethod
    def get_user_combination_history(
        user_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> Dict:
        """
        获取用户的组合使用历史

        Args:
            user_id: 用户ID
            page: 页码
            page_size: 每页大小

        Returns:
            历史记录列表和分页信息
        """
        session = SessionLocal()
        try:
            query = session.query(PromptCombinationLog).filter(
                PromptCombinationLog.user_id == user_id
            ).order_by(
                PromptCombinationLog.created_at.desc()
            )

            total = query.count()
            offset = (page - 1) * page_size
            logs = query.offset(offset).limit(page_size).all()

            return {
                'logs': [log.to_dict() for log in logs],
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }
        finally:
            session.close()
