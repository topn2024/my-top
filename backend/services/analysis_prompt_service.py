#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析提示词服务
提供分析提示词的CRUD操作和业务逻辑
"""
import json
from typing import List, Dict, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import SessionLocal
from models import AnalysisPrompt

try:
    from logger_config import log_service_call
except ImportError:
    # 如果没有 log_service_call，创建一个空装饰器
    def log_service_call(name):
        def decorator(func):
            return func
        return decorator


class AnalysisPromptService:
    """分析提示词服务类"""

    @staticmethod


    @log_service_call("查询分析提示词列表")
    def list_prompts(
        status: Optional[str] = None,
        industry_tag: Optional[str] = None,
        search_keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict:
        """
        列出分析提示词

        Args:
            status: 状态筛选 (draft/active/archived)
            industry_tag: 行业标签筛选
            search_keyword: 搜索关键词 (匹配name或description)
            page: 页码
            page_size: 每页大小

        Returns:
            包含prompts列表和分页信息的字典
        """
        session = SessionLocal()
        try:
            query = session.query(AnalysisPrompt)

            # 状态筛选
            if status:
                query = query.filter(AnalysisPrompt.status == status)

            # 行业标签筛选
            if industry_tag:
                query = query.filter(AnalysisPrompt.industry_tags.like(f'%"{industry_tag}"%'))

            # 关键词搜索
            if search_keyword:
                query = query.filter(
                    (AnalysisPrompt.name.like(f'%{search_keyword}%')) |
                    (AnalysisPrompt.description.like(f'%{search_keyword}%'))
                )

            # 排序：默认在前，使用次数降序
            query = query.order_by(
                AnalysisPrompt.is_default.desc(),
                AnalysisPrompt.usage_count.desc()
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


    @log_service_call("获取分析提示词")
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
            prompt = session.query(AnalysisPrompt).filter(
                AnalysisPrompt.id == prompt_id
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
            prompt = session.query(AnalysisPrompt).filter(
                AnalysisPrompt.code == code
            ).first()

            return prompt.to_dict() if prompt else None
        finally:
            session.close()

    @staticmethod
    def get_default_prompt(industry_tag: Optional[str] = None) -> Optional[Dict]:
        """
        获取默认提示词

        Args:
            industry_tag: 行业标签（可选，用于获取特定行业的默认提示词）

        Returns:
            默认提示词字典或None
        """
        session = SessionLocal()
        try:
            query = session.query(AnalysisPrompt).filter(
                AnalysisPrompt.is_default == True,
                AnalysisPrompt.status == 'active'
            )

            # 如果指定行业，优先匹配
            if industry_tag:
                industry_prompt = query.filter(
                    AnalysisPrompt.industry_tags.like(f'%"{industry_tag}"%')
                ).first()
                if industry_prompt:
                    return industry_prompt.to_dict()

            # 否则返回任一默认提示词
            prompt = query.first()
            return prompt.to_dict() if prompt else None
        finally:
            session.close()

    @staticmethod


    @log_service_call("创建分析提示词")
    def create_prompt(data: Dict, created_by: Optional[int] = None) -> Dict:
        """
        创建新的分析提示词

        Args:
            data: 提示词数据
            created_by: 创建者ID

        Returns:
            创建的提示词字典
        """
        session = SessionLocal()
        try:
            # 准备数据
            prompt_data = {
                'name': data['name'],
                'code': data['code'],
                'description': data.get('description', ''),
                'system_prompt': data['system_prompt'],
                'user_template': data['user_template'],
                'variables': json.dumps(data.get('variables', [])),
                'temperature': data.get('temperature', 0.7),
                'max_tokens': data.get('max_tokens', 2000),
                'model': data.get('model', 'glm-4-flash'),
                'category_id': data.get('category_id'),
                'industry_tags': json.dumps(data.get('industry_tags', [])),
                'keywords': json.dumps(data.get('keywords', [])),
                'status': data.get('status', 'draft'),
                'version': data.get('version', '1.0'),
                'is_default': data.get('is_default', False),
                'example_company': data.get('example_company'),
                'example_output': data.get('example_output'),
                'notes': data.get('notes'),
                'created_by': created_by,
                'updated_by': created_by
            }

            prompt = AnalysisPrompt(**prompt_data)
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


    @log_service_call("更新分析提示词")
    def update_prompt(prompt_id: int, data: Dict, updated_by: Optional[int] = None) -> Optional[Dict]:
        """
        更新分析提示词

        Args:
            prompt_id: 提示词ID
            data: 更新数据
            updated_by: 更新者ID

        Returns:
            更新后的提示词字典或None
        """
        session = SessionLocal()
        try:
            prompt = session.query(AnalysisPrompt).filter(
                AnalysisPrompt.id == prompt_id
            ).first()

            if not prompt:
                return None

            # 更新字段
            updateable_fields = [
                'name', 'description', 'system_prompt', 'user_template',
                'temperature', 'max_tokens', 'model', 'category_id',
                'status', 'version', 'is_default',
                'example_company', 'example_output', 'notes'
            ]

            for field in updateable_fields:
                if field in data:
                    setattr(prompt, field, data[field])

            # JSON字段特殊处理
            if 'variables' in data:
                prompt.variables = json.dumps(data['variables'])
            if 'industry_tags' in data:
                prompt.industry_tags = json.dumps(data['industry_tags'])
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
        删除分析提示词（软删除，改为archived状态）

        Args:
            prompt_id: 提示词ID

        Returns:
            是否成功
        """
        session = SessionLocal()
        try:
            prompt = session.query(AnalysisPrompt).filter(
                AnalysisPrompt.id == prompt_id
            ).first()

            if not prompt:
                return False

            # 软删除：修改状态为archived
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
                text("UPDATE analysis_prompts SET usage_count = usage_count + 1 WHERE id = :id"),
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
        更新统计信息（成功率和评分）

        Args:
            prompt_id: 提示词ID
            success: 是否成功
            rating: 用户评分 (1-5)

        Returns:
            是否成功
        """
        session = SessionLocal()
        try:
            prompt = session.query(AnalysisPrompt).filter(
                AnalysisPrompt.id == prompt_id
            ).first()

            if not prompt:
                return False

            # 更新成功率（简单移动平均）
            total_uses = prompt.usage_count or 1
            current_success_rate = prompt.success_rate or 0.0
            new_success_value = 1.0 if success else 0.0
            prompt.success_rate = (current_success_rate * (total_uses - 1) + new_success_value) / total_uses

            # 更新评分（如果提供）
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
    def get_available_industry_tags() -> List[str]:
        """
        获取所有已使用的行业标签

        Returns:
            行业标签列表
        """
        session = SessionLocal()
        try:
            prompts = session.query(AnalysisPrompt.industry_tags).filter(
                AnalysisPrompt.industry_tags.isnot(None)
            ).all()

            tags = set()
            for prompt in prompts:
                if prompt.industry_tags:
                    try:
                        tag_list = json.loads(prompt.industry_tags)
                        tags.update(tag_list)
                    except:
                        pass

            return sorted(list(tags))
        finally:
            session.close()
