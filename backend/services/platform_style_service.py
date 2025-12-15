#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
平台风格提示词服务
提供平台风格提示词的CRUD操作和风格应用逻辑
"""
import json
from typing import List, Dict, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import SessionLocal
from models_prompt_v2 import PlatformStylePrompt


class PlatformStyleService:
    """平台风格提示词服务类"""

    # 支持的平台
    SUPPORTED_PLATFORMS = ['zhihu', 'csdn', 'juejin', 'xiaohongshu']

    @staticmethod
    def list_prompts(
        platform: Optional[str] = None,
        status: Optional[str] = None,
        apply_stage: Optional[str] = None,
        search_keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict:
        """
        列出平台风格提示词

        Args:
            platform: 平台筛选 (zhihu/csdn/juejin/xiaohongshu)
            status: 状态筛选
            apply_stage: 应用阶段筛选 (generation/publish/both)
            search_keyword: 搜索关键词
            page: 页码
            page_size: 每页大小

        Returns:
            包含prompts列表和分页信息的字典
        """
        session = SessionLocal()
        try:
            query = session.query(PlatformStylePrompt)

            # 平台筛选
            if platform:
                query = query.filter(PlatformStylePrompt.platform == platform)

            # 状态筛选
            if status:
                query = query.filter(PlatformStylePrompt.status == status)

            # 应用阶段筛选
            if apply_stage:
                query = query.filter(PlatformStylePrompt.apply_stage.in_([apply_stage, 'both']))

            # 关键词搜索
            if search_keyword:
                query = query.filter(
                    (PlatformStylePrompt.name.like(f'%{search_keyword}%')) |
                    (PlatformStylePrompt.description.like(f'%{search_keyword}%'))
                )

            # 排序
            query = query.order_by(
                PlatformStylePrompt.platform,
                PlatformStylePrompt.is_default.desc(),
                PlatformStylePrompt.avg_rating.desc()
            )

            # 分页
            total = query.count()
            offset = (page - 1) * page_size
            prompts = query.offset(offset).limit(page_size).all()

            return {
                'prompts': [p.to_dict() for p in prompts],
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }
        finally:
            session.close()

    @staticmethod
    def get_prompt(prompt_id: int) -> Optional[Dict]:
        """
        获取单个提示词详情

        Args:
            prompt_id: 提示词ID

        Returns:
            提示词字典或None
        """
        session = SessionLocal()
        try:
            prompt = session.query(PlatformStylePrompt).filter(
                PlatformStylePrompt.id == prompt_id
            ).first()

            return prompt.to_dict() if prompt else None
        finally:
            session.close()

    @staticmethod
    def get_prompt_by_code(code: str) -> Optional[Dict]:
        """
        根据代码获取提示词

        Args:
            code: 提示词代码

        Returns:
            提示词字典或None
        """
        session = SessionLocal()
        try:
            prompt = session.query(PlatformStylePrompt).filter(
                PlatformStylePrompt.code == code
            ).first()

            return prompt.to_dict() if prompt else None
        finally:
            session.close()

    @staticmethod
    def get_styles_by_platform(platform: str, apply_stage: Optional[str] = None) -> List[Dict]:
        """
        根据平台获取所有风格提示词

        Args:
            platform: 平台名称 (zhihu/csdn/juejin/xiaohongshu)
            apply_stage: 应用阶段筛选

        Returns:
            提示词列表
        """
        session = SessionLocal()
        try:
            query = session.query(PlatformStylePrompt).filter(
                PlatformStylePrompt.platform == platform,
                PlatformStylePrompt.status == 'active'
            )

            # 如果指定应用阶段，筛选匹配的提示词
            if apply_stage:
                query = query.filter(
                    PlatformStylePrompt.apply_stage.in_([apply_stage, 'both'])
                )

            # 排序：默认在前
            query = query.order_by(
                PlatformStylePrompt.is_default.desc(),
                PlatformStylePrompt.avg_rating.desc()
            )

            prompts = query.all()
            return [p.to_dict() for p in prompts]
        finally:
            session.close()

    @staticmethod
    def get_default_style(platform: str, apply_stage: Optional[str] = None) -> Optional[Dict]:
        """
        获取平台的默认风格

        Args:
            platform: 平台名称
            apply_stage: 应用阶段

        Returns:
            默认风格字典或None
        """
        session = SessionLocal()
        try:
            query = session.query(PlatformStylePrompt).filter(
                PlatformStylePrompt.platform == platform,
                PlatformStylePrompt.is_default == True,
                PlatformStylePrompt.status == 'active'
            )

            # 如果指定应用阶段，筛选匹配的提示词
            if apply_stage:
                query = query.filter(
                    PlatformStylePrompt.apply_stage.in_([apply_stage, 'both'])
                )

            prompt = query.first()
            return prompt.to_dict() if prompt else None
        finally:
            session.close()

    @staticmethod
    def create_prompt(data: Dict, created_by: Optional[int] = None) -> Dict:
        """
        创建新的平台风格提示词

        Args:
            data: 提示词数据
            created_by: 创建者ID

        Returns:
            创建的提示词字典
        """
        session = SessionLocal()
        try:
            prompt_data = {
                'name': data['name'],
                'code': data['code'],
                'description': data.get('description', ''),
                'platform': data['platform'],
                'platform_display_name': data.get('platform_display_name', ''),
                'system_prompt': data['system_prompt'],
                'user_template': data['user_template'],
                'variables': json.dumps(data.get('variables', [])),
                'style_features': json.dumps(data.get('style_features', {})),
                'formatting_rules': json.dumps(data.get('formatting_rules', {})),
                'temperature': data.get('temperature', 0.7),
                'max_tokens': data.get('max_tokens', 3000),
                'model': data.get('model', 'glm-4-flash'),
                'apply_stage': data.get('apply_stage', 'both'),
                'status': data.get('status', 'draft'),
                'version': data.get('version', '1.0'),
                'is_default': data.get('is_default', False),
                'example_before': data.get('example_before'),
                'example_after': data.get('example_after'),
                'notes': data.get('notes'),
                'created_by': created_by,
                'updated_by': created_by
            }

            prompt = PlatformStylePrompt(**prompt_data)
            session.add(prompt)
            session.commit()
            session.refresh(prompt)

            return prompt.to_dict()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @staticmethod
    def update_prompt(prompt_id: int, data: Dict, updated_by: Optional[int] = None) -> Optional[Dict]:
        """
        更新平台风格提示词

        Args:
            prompt_id: 提示词ID
            data: 更新数据
            updated_by: 更新者ID

        Returns:
            更新后的提示词字典或None
        """
        session = SessionLocal()
        try:
            prompt = session.query(PlatformStylePrompt).filter(
                PlatformStylePrompt.id == prompt_id
            ).first()

            if not prompt:
                return None

            # 更新基本字段
            updateable_fields = [
                'name', 'description', 'platform', 'platform_display_name',
                'system_prompt', 'user_template',
                'temperature', 'max_tokens', 'model', 'apply_stage',
                'status', 'version', 'is_default',
                'example_before', 'example_after', 'notes'
            ]

            for field in updateable_fields:
                if field in data:
                    setattr(prompt, field, data[field])

            # JSON字段特殊处理
            if 'variables' in data:
                prompt.variables = json.dumps(data['variables'])
            if 'style_features' in data:
                prompt.style_features = json.dumps(data['style_features'])
            if 'formatting_rules' in data:
                prompt.formatting_rules = json.dumps(data['formatting_rules'])

            if updated_by:
                prompt.updated_by = updated_by

            session.commit()
            session.refresh(prompt)

            return prompt.to_dict()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @staticmethod
    def delete_prompt(prompt_id: int) -> bool:
        """
        删除平台风格提示词（软删除）

        Args:
            prompt_id: 提示词ID

        Returns:
            是否成功
        """
        session = SessionLocal()
        try:
            prompt = session.query(PlatformStylePrompt).filter(
                PlatformStylePrompt.id == prompt_id
            ).first()

            if not prompt:
                return False

            prompt.status = 'archived'
            session.commit()

            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @staticmethod
    def increment_usage(prompt_id: int) -> bool:
        """
        增加使用次数

        Args:
            prompt_id: 提示词ID

        Returns:
            是否成功
        """
        session = SessionLocal()
        try:
            session.execute(
                text("UPDATE platform_style_prompts SET usage_count = usage_count + 1 WHERE id = :id"),
                {'id': prompt_id}
            )
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @staticmethod
    def update_statistics(prompt_id: int, success: bool, rating: Optional[int] = None) -> bool:
        """
        更新统计信息

        Args:
            prompt_id: 提示词ID
            success: 是否成功
            rating: 用户评分 (1-5)

        Returns:
            是否成功
        """
        session = SessionLocal()
        try:
            prompt = session.query(PlatformStylePrompt).filter(
                PlatformStylePrompt.id == prompt_id
            ).first()

            if not prompt:
                return False

            total_uses = prompt.usage_count or 1
            current_success_rate = prompt.success_rate or 0.0
            new_success_value = 1.0 if success else 0.0
            prompt.success_rate = (current_success_rate * (total_uses - 1) + new_success_value) / total_uses

            if rating is not None and 1 <= rating <= 5:
                current_avg = prompt.avg_rating or 0.0
                prompt.avg_rating = (current_avg * (total_uses - 1) + rating) / total_uses

            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @staticmethod
    def get_all_platforms() -> List[Dict]:
        """
        获取所有平台及其默认风格

        Returns:
            平台列表，每个平台包含code、name、default_style_id
        """
        platforms = []

        for platform_code in PlatformStyleService.SUPPORTED_PLATFORMS:
            default_style = PlatformStyleService.get_default_style(platform_code)

            platform_names = {
                'zhihu': '知乎',
                'csdn': 'CSDN',
                'juejin': '掘金',
                'xiaohongshu': '小红书'
            }

            platforms.append({
                'code': platform_code,
                'name': platform_names.get(platform_code, platform_code),
                'default_style_id': default_style['id'] if default_style else None,
                'default_style_name': default_style['name'] if default_style else None
            })

        return platforms
