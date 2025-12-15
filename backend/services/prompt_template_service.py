#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提示词模板服务
提供模板的CRUD操作和管理功能
"""
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger_config import setup_logger, log_service_call
from typing import List, Dict, Optional
from models import SessionLocal
from models_prompt_template import PromptTemplate, PromptTemplateCategory, PromptTemplateAuditLog
from sqlalchemy import text

logger = setup_logger(__name__)


class PromptTemplateService:
    """提示词模板管理服务"""

    @staticmethod
    @log_service_call("查询提示词模板列表")
    def list_templates(status: str = None, category_id: int = None,
                      industry: str = None, platform: str = None) -> List[Dict]:
        """
        列出模板

        Args:
            status: 状态过滤 (active/draft/archived)
            category_id: 分类ID
            industry: 行业标签
            platform: 平台标签

        Returns:
            模板列表
        """
        session = SessionLocal()
        try:
            query = session.query(PromptTemplate)

            if status:
                query = query.filter_by(status=status)
            if category_id:
                query = query.filter_by(category_id=category_id)

            templates = query.order_by(PromptTemplate.created_at.desc()).all()

            # 前端过滤（JSON字段）
            results = []
            for t in templates:
                # 行业过滤
                if industry and t.industry_tags:
                    if industry not in t.industry_tags:
                        continue

                # 平台过滤
                if platform and t.platform_tags:
                    if platform not in t.platform_tags:
                        continue

                results.append(t.to_dict(include_prompts=False))

            return results

        finally:
            session.close()

    @staticmethod
    @log_service_call("获取提示词模板")
    def get_template(template_id: int, include_prompts: bool = True) -> Optional[Dict]:
        """获取模板详情"""
        session = SessionLocal()
        try:
            template = session.query(PromptTemplate).get(template_id)
            if not template:
                return None
            return template.to_dict(include_prompts=include_prompts)
        finally:
            session.close()

    @staticmethod
    def get_template_by_code(code: str) -> Optional[Dict]:
        """通过代码获取模板"""
        session = SessionLocal()
        try:
            template = session.query(PromptTemplate).filter_by(code=code).first()
            if not template:
                return None
            return template.to_dict()
        finally:
            session.close()

    @staticmethod
    @log_service_call("创建提示词模板")
    def create_template(data: Dict, user_id: int) -> Dict:
        """
        创建模板

        Args:
            data: 模板数据
            user_id: 创建者ID

        Returns:
            创建的模板
        """
        session = SessionLocal()
        try:
            template = PromptTemplate(
                name=data['name'],
                code=data['code'],
                category_id=data.get('category_id'),
                prompts=data['prompts'],
                industry_tags=data.get('industry_tags', []),
                platform_tags=data.get('platform_tags', []),
                keywords=data.get('keywords', []),
                ai_config=data.get('ai_config', {}),
                version=data.get('version', '1.0'),
                status=data.get('status', 'draft'),
                description=data.get('description'),
                example_company=data.get('example_company'),
                example_output=data.get('example_output'),
                notes=data.get('notes'),
                created_by=user_id
            )

            session.add(template)
            session.commit()
            session.refresh(template)

            # 记录审计日志
            PromptTemplateService._log_audit(
                session, template.id, user_id, 'create',
                f'Created template: {template.name}'
            )

            return template.to_dict()

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create template: {e}")
            raise
        finally:
            session.close()

    @staticmethod
    @log_service_call("更新提示词模板")
    def update_template(template_id: int, data: Dict, user_id: int) -> Dict:
        """更新模板"""
        session = SessionLocal()
        try:
            template = session.query(PromptTemplate).get(template_id)
            if not template:
                raise ValueError(f"Template {template_id} not found")

            # 记录变更
            changes = {}
            for key in ['name', 'prompts', 'industry_tags', 'platform_tags',
                       'keywords', 'ai_config', 'description', 'status']:
                if key in data:
                    old_value = getattr(template, key)
                    new_value = data[key]
                    if old_value != new_value:
                        changes[key] = {'old': old_value, 'new': new_value}
                        setattr(template, key, new_value)

            template.updated_by = user_id
            session.commit()
            session.refresh(template)

            # 记录审计日志
            if changes:
                PromptTemplateService._log_audit(
                    session, template.id, user_id, 'update',
                    f'Updated template: {template.name}',
                    changes
                )

            return template.to_dict()

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update template: {e}")
            raise
        finally:
            session.close()

    @staticmethod
    def delete_template(template_id: int, user_id: int) -> bool:
        """删除模板"""
        session = SessionLocal()
        try:
            template = session.query(PromptTemplate).get(template_id)
            if not template:
                return False

            template_name = template.name
            session.delete(template)
            session.commit()

            # 记录审计日志
            PromptTemplateService._log_audit(
                session, template_id, user_id, 'delete',
                f'Deleted template: {template_name}'
            )

            return True

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to delete template: {e}")
            raise
        finally:
            session.close()

    @staticmethod
    def activate_template(template_id: int, user_id: int) -> Dict:
        """激活模板"""
        return PromptTemplateService.update_template(
            template_id, {'status': 'active'}, user_id
        )

    @staticmethod
    def archive_template(template_id: int, user_id: int) -> Dict:
        """归档模板"""
        return PromptTemplateService.update_template(
            template_id, {'status': 'archived'}, user_id
        )

    @staticmethod
    def list_categories() -> List[Dict]:
        """列出所有分类"""
        session = SessionLocal()
        try:
            categories = session.query(PromptTemplateCategory).order_by(
                PromptTemplateCategory.sort_order
            ).all()
            return [c.to_dict() for c in categories]
        finally:
            session.close()

    @staticmethod
    def get_category(category_id: int) -> Optional[Dict]:
        """获取分类详情"""
        session = SessionLocal()
        try:
            category = session.query(PromptTemplateCategory).get(category_id)
            if not category:
                return None
            return category.to_dict()
        finally:
            session.close()

    @staticmethod
    def _log_audit(session, template_id: int, user_id: int, action: str,
                   detail: str, changes: Dict = None):
        """记录审计日志"""
        try:
            log = PromptTemplateAuditLog(
                template_id=template_id,
                user_id=user_id,
                action=action,
                action_detail=detail,
                changes=changes or {}
            )
            session.add(log)
            session.commit()
        except Exception as e:
            logger.warning(f"Failed to log audit: {e}")

    @staticmethod
    def get_audit_logs(template_id: int, limit: int = 50) -> List[Dict]:
        """获取模板的审计日志"""
        session = SessionLocal()
        try:
            logs = session.query(PromptTemplateAuditLog).filter_by(
                template_id=template_id
            ).order_by(
                PromptTemplateAuditLog.created_at.desc()
            ).limit(limit).all()

            return [log.to_dict() for log in logs]
        finally:
            session.close()

    @staticmethod
    def increment_usage_count(template_id: int):
        """增加模板使用次数"""
        session = SessionLocal()
        try:
            session.execute(
                text("UPDATE prompt_templates SET usage_count = usage_count + 1 WHERE id = :id"),
                {'id': template_id}
            )
            session.commit()
        except Exception as e:
            logger.warning(f"Failed to increment usage count: {e}")
        finally:
            session.close()
