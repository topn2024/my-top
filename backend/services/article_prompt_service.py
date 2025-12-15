#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文章生成提示词服务
提供文章生成提示词的CRUD操作和业务逻辑
"""
import json
from typing import List, Dict, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import SessionLocal
from models_prompt_v2 import ArticlePrompt


class ArticlePromptService:
    """文章生成提示词服务类"""

    @staticmethod


    @log_service_call("查询文章提示词列表")
    def list_prompts(
        status: Optional[str] = None,
        industry_tag: Optional[str] = None,
        style_tag: Optional[str] = None,
        search_keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict:
        """
        列出文章生成提示词

        Args:
            status: 状态筛选 (draft/active/archived)
            industry_tag: 行业标签筛选
            style_tag: 风格标签筛选
            search_keyword: 搜索关键词
            page: 页码
            page_size: 每页大小

        Returns:
            包含prompts列表和分页信息的字典
        """
        session = SessionLocal()
        try:
            query = session.query(ArticlePrompt)

            # 状态筛选
            if status:
                query = query.filter(ArticlePrompt.status == status)

            # 行业标签筛选
            if industry_tag:
                query = query.filter(ArticlePrompt.industry_tags.like(f'%"{industry_tag}"%'))

            # 风格标签筛选
            if style_tag:
                query = query.filter(ArticlePrompt.style_tags.like(f'%"{style_tag}"%'))

            # 关键词搜索
            if search_keyword:
                query = query.filter(
                    (ArticlePrompt.name.like(f'%{search_keyword}%')) |
                    (ArticlePrompt.description.like(f'%{search_keyword}%'))
                )

            # 排序
            query = query.order_by(
                ArticlePrompt.is_default.desc(),
                ArticlePrompt.avg_rating.desc(),
                ArticlePrompt.usage_count.desc()
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


    @log_service_call("获取文章提示词")
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
            prompt = session.query(ArticlePrompt).filter(
                ArticlePrompt.id == prompt_id
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
            prompt = session.query(ArticlePrompt).filter(
                ArticlePrompt.code == code
            ).first()

            return prompt.to_dict() if prompt else None
        finally:
            session.close()

    @staticmethod
    def get_default_prompt(industry_tag: Optional[str] = None, style_tag: Optional[str] = None) -> Optional[Dict]:
        """
        获取默认提示词

        Args:
            industry_tag: 行业标签
            style_tag: 风格标签

        Returns:
            默认提示词字典或None
        """
        session = SessionLocal()
        try:
            query = session.query(ArticlePrompt).filter(
                ArticlePrompt.is_default == True,
                ArticlePrompt.status == 'active'
            )

            # 如果指定行业和风格，优先匹配
            if industry_tag and style_tag:
                matched = query.filter(
                    ArticlePrompt.industry_tags.like(f'%"{industry_tag}"%'),
                    ArticlePrompt.style_tags.like(f'%"{style_tag}"%')
                ).first()
                if matched:
                    return matched.to_dict()

            # 只匹配行业
            if industry_tag:
                matched = query.filter(
                    ArticlePrompt.industry_tags.like(f'%"{industry_tag}"%')
                ).first()
                if matched:
                    return matched.to_dict()

            # 返回任一默认提示词
            prompt = query.first()
            return prompt.to_dict() if prompt else None
        finally:
            session.close()

    @staticmethod


    @log_service_call("创建文章提示词")
    def create_prompt(data: Dict, created_by: Optional[int] = None) -> Dict:
        """
        创建新的文章生成提示词

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
                'system_prompt': data['system_prompt'],
                'user_template': data['user_template'],
                'variables': json.dumps(data.get('variables', [])),
                'default_angles': json.dumps(data.get('default_angles', [])),
                'article_structure': json.dumps(data.get('article_structure', {})),
                'temperature': data.get('temperature', 0.8),
                'max_tokens': data.get('max_tokens', 3000),
                'model': data.get('model', 'glm-4-flash'),
                'category_id': data.get('category_id'),
                'industry_tags': json.dumps(data.get('industry_tags', [])),
                'style_tags': json.dumps(data.get('style_tags', [])),
                'keywords': json.dumps(data.get('keywords', [])),
                'status': data.get('status', 'draft'),
                'version': data.get('version', '1.0'),
                'is_default': data.get('is_default', False),
                'example_input': data.get('example_input'),
                'example_output': data.get('example_output'),
                'notes': data.get('notes'),
                'created_by': created_by,
                'updated_by': created_by
            }

            prompt = ArticlePrompt(**prompt_data)
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


    @log_service_call("更新文章提示词")
    def update_prompt(prompt_id: int, data: Dict, updated_by: Optional[int] = None) -> Optional[Dict]:
        """
        更新文章生成提示词

        Args:
            prompt_id: 提示词ID
            data: 更新数据
            updated_by: 更新者ID

        Returns:
            更新后的提示词字典或None
        """
        session = SessionLocal()
        try:
            prompt = session.query(ArticlePrompt).filter(
                ArticlePrompt.id == prompt_id
            ).first()

            if not prompt:
                return None

            # 更新基本字段
            updateable_fields = [
                'name', 'description', 'system_prompt', 'user_template',
                'temperature', 'max_tokens', 'model', 'category_id',
                'status', 'version', 'is_default',
                'example_input', 'example_output', 'notes'
            ]

            for field in updateable_fields:
                if field in data:
                    setattr(prompt, field, data[field])

            # JSON字段特殊处理
            if 'variables' in data:
                prompt.variables = json.dumps(data['variables'])
            if 'default_angles' in data:
                prompt.default_angles = json.dumps(data['default_angles'])
            if 'article_structure' in data:
                prompt.article_structure = json.dumps(data['article_structure'])
            if 'industry_tags' in data:
                prompt.industry_tags = json.dumps(data['industry_tags'])
            if 'style_tags' in data:
                prompt.style_tags = json.dumps(data['style_tags'])
            if 'keywords' in data:
                prompt.keywords = json.dumps(data['keywords'])

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
        删除文章生成提示词（软删除）

        Args:
            prompt_id: 提示词ID

        Returns:
            是否成功
        """
        session = SessionLocal()
        try:
            prompt = session.query(ArticlePrompt).filter(
                ArticlePrompt.id == prompt_id
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
                text("UPDATE article_prompts SET usage_count = usage_count + 1 WHERE id = :id"),
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
            prompt = session.query(ArticlePrompt).filter(
                ArticlePrompt.id == prompt_id
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
    def get_available_tags() -> Dict[str, List[str]]:
        """
        获取所有已使用的标签

        Returns:
            包含industry_tags和style_tags的字典
        """
        session = SessionLocal()
        try:
            prompts = session.query(
                ArticlePrompt.industry_tags,
                ArticlePrompt.style_tags
            ).filter(
                (ArticlePrompt.industry_tags.isnot(None)) |
                (ArticlePrompt.style_tags.isnot(None))
            ).all()

            industry_tags = set()
            style_tags = set()

            for prompt in prompts:
                if prompt.industry_tags:
                    try:
                        tags = json.loads(prompt.industry_tags)
                        industry_tags.update(tags)
                    except:
                        pass

                if prompt.style_tags:
                    try:
                        tags = json.loads(prompt.style_tags)
                        style_tags.update(tags)
                    except:
                        pass

            return {
                'industry_tags': sorted(list(industry_tags)),
                'style_tags': sorted(list(style_tags))
            }
        finally:
            session.close()
