#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三模块提示词系统 - 数据库模型
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, ForeignKey, Float, func
from sqlalchemy.orm import relationship
from models import Base
import json


class AnalysisPrompt(Base):
    """分析提示词表"""
    __tablename__ = 'analysis_prompts'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 基本信息
    name = Column(String(200), nullable=False)
    code = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text)

    # 提示词内容
    system_prompt = Column(Text, nullable=False)
    user_template = Column(Text, nullable=False)
    variables = Column(Text)  # JSON字符串

    # AI配置
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=2000)
    model = Column(String(50), default='glm-4-flash')

    # 分类和标签
    category_id = Column(Integer, nullable=True)
    industry_tags = Column(Text)  # JSON字符串
    keywords = Column(Text)  # JSON字符串

    # 状态
    status = Column(String(20), default='draft', index=True)
    version = Column(String(20), default='1.0')
    is_default = Column(Boolean, default=False)

    # 统计
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    avg_rating = Column(Float, default=0.0)

    # 示例
    example_company = Column(String(200))
    example_output = Column(Text)
    notes = Column(Text)

    # 审计
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'system_prompt': self.system_prompt,
            'user_template': self.user_template,
            'variables': json.loads(self.variables) if self.variables else [],
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'model': self.model,
            'category_id': self.category_id,
            'industry_tags': json.loads(self.industry_tags) if self.industry_tags else [],
            'keywords': json.loads(self.keywords) if self.keywords else [],
            'status': self.status,
            'version': self.version,
            'is_default': self.is_default,
            'usage_count': self.usage_count,
            'success_rate': self.success_rate,
            'avg_rating': self.avg_rating,
            'example_company': self.example_company,
            'example_output': self.example_output,
            'notes': self.notes,
            'created_by': self.created_by,
            'updated_by': self.updated_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ArticlePrompt(Base):
    """文章生成提示词表"""
    __tablename__ = 'article_prompts'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 基本信息
    name = Column(String(200), nullable=False)
    code = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text)

    # 提示词内容
    system_prompt = Column(Text, nullable=False)
    user_template = Column(Text, nullable=False)
    variables = Column(Text)  # JSON字符串

    # 文章生成特定配置
    default_angles = Column(Text)  # JSON字符串
    article_structure = Column(Text)  # JSON字符串

    # AI配置
    temperature = Column(Float, default=0.8)
    max_tokens = Column(Integer, default=3000)
    model = Column(String(50), default='glm-4-flash')

    # 分类和标签
    category_id = Column(Integer, nullable=True)
    industry_tags = Column(Text)  # JSON字符串
    style_tags = Column(Text)  # JSON字符串
    keywords = Column(Text)  # JSON字符串

    # 状态
    status = Column(String(20), default='draft', index=True)
    version = Column(String(20), default='1.0')
    is_default = Column(Boolean, default=False)

    # 统计
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    avg_rating = Column(Float, default=0.0)

    # 示例
    example_input = Column(Text)
    example_output = Column(Text)
    notes = Column(Text)

    # 审计
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'system_prompt': self.system_prompt,
            'user_template': self.user_template,
            'variables': json.loads(self.variables) if self.variables else [],
            'default_angles': json.loads(self.default_angles) if self.default_angles else [],
            'article_structure': json.loads(self.article_structure) if self.article_structure else {},
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'model': self.model,
            'category_id': self.category_id,
            'industry_tags': json.loads(self.industry_tags) if self.industry_tags else [],
            'style_tags': json.loads(self.style_tags) if self.style_tags else [],
            'keywords': json.loads(self.keywords) if self.keywords else [],
            'status': self.status,
            'version': self.version,
            'is_default': self.is_default,
            'usage_count': self.usage_count,
            'success_rate': self.success_rate,
            'avg_rating': self.avg_rating,
            'example_input': self.example_input,
            'example_output': self.example_output,
            'notes': self.notes,
            'created_by': self.created_by,
            'updated_by': self.updated_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class PlatformStylePrompt(Base):
    """平台风格提示词表"""
    __tablename__ = 'platform_style_prompts'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 基本信息
    name = Column(String(200), nullable=False)
    code = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text)

    # 平台信息
    platform = Column(String(50), nullable=False, index=True)  # zhihu/csdn/juejin/xiaohongshu
    platform_display_name = Column(String(100))

    # 提示词内容
    system_prompt = Column(Text, nullable=False)
    user_template = Column(Text, nullable=False)
    variables = Column(Text)  # JSON字符串

    # 平台风格特征
    style_features = Column(Text)  # JSON字符串
    formatting_rules = Column(Text)  # JSON字符串

    # AI配置
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=3000)
    model = Column(String(50), default='glm-4-flash')

    # 应用阶段
    apply_stage = Column(String(20), default='both')  # generation/publish/both

    # 状态
    status = Column(String(20), default='draft', index=True)
    version = Column(String(20), default='1.0')
    is_default = Column(Boolean, default=False)

    # 统计
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    avg_rating = Column(Float, default=0.0)

    # 示例
    example_before = Column(Text)
    example_after = Column(Text)
    notes = Column(Text)

    # 审计
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'platform': self.platform,
            'platform_display_name': self.platform_display_name,
            'system_prompt': self.system_prompt,
            'user_template': self.user_template,
            'variables': json.loads(self.variables) if self.variables else [],
            'style_features': json.loads(self.style_features) if self.style_features else {},
            'formatting_rules': json.loads(self.formatting_rules) if self.formatting_rules else {},
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'model': self.model,
            'apply_stage': self.apply_stage,
            'status': self.status,
            'version': self.version,
            'is_default': self.is_default,
            'usage_count': self.usage_count,
            'success_rate': self.success_rate,
            'avg_rating': self.avg_rating,
            'example_before': self.example_before,
            'example_after': self.example_after,
            'notes': self.notes,
            'created_by': self.created_by,
            'updated_by': self.updated_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class PromptCombinationLog(Base):
    """提示词组合使用记录表"""
    __tablename__ = 'prompt_combination_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 关联
    user_id = Column(Integer, nullable=False, index=True)
    workflow_id = Column(Integer, nullable=True, index=True)

    # 使用的提示词ID
    analysis_prompt_id = Column(Integer, nullable=True)
    article_prompt_id = Column(Integer, nullable=True)
    platform_style_prompt_id = Column(Integer, nullable=True)

    # 选择方式
    selection_method = Column(String(20))  # manual/auto/recommended

    # 应用阶段
    applied_at_generation = Column(Boolean, default=False)
    applied_at_publish = Column(Boolean, default=False)

    # 结果
    status = Column(String(20))  # success/failed/partial
    articles_generated = Column(Integer, default=0)
    articles_published = Column(Integer, default=0)
    error_message = Column(Text)

    # 反馈
    user_rating = Column(Integer)
    user_feedback = Column(Text)

    # 时间
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'workflow_id': self.workflow_id,
            'analysis_prompt_id': self.analysis_prompt_id,
            'article_prompt_id': self.article_prompt_id,
            'platform_style_prompt_id': self.platform_style_prompt_id,
            'selection_method': self.selection_method,
            'applied_at_generation': self.applied_at_generation,
            'applied_at_publish': self.applied_at_publish,
            'status': self.status,
            'articles_generated': self.articles_generated,
            'articles_published': self.articles_published,
            'error_message': self.error_message,
            'user_rating': self.user_rating,
            'user_feedback': self.user_feedback,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
