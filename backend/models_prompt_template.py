#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提示词模板管理系统 - 数据库模型扩展
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, ForeignKey, JSON, Float, func
from sqlalchemy.orm import relationship
from models import Base


class PromptTemplateCategory(Base):
    """提示词模板分类表"""
    __tablename__ = 'prompt_template_categories'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)  # 分类名称
    code = Column(String(50), nullable=False, unique=True, index=True)  # 分类代码
    description = Column(Text)  # 分类描述
    parent_id = Column(Integer, ForeignKey('prompt_template_categories.id'), nullable=True)  # 支持层级
    sort_order = Column(Integer, default=0)  # 排序
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # 关系
    children = relationship("PromptTemplateCategory",
                          backref='parent',
                          remote_side=[id])
    templates = relationship("PromptTemplate", back_populates="category")

    def __repr__(self):
        return f"<PromptTemplateCategory(id={self.id}, name='{self.name}', code='{self.code}')>"

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'parent_id': self.parent_id,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class PromptTemplate(Base):
    """提示词模板表"""
    __tablename__ = 'prompt_templates'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, index=True)  # 模板名称
    code = Column(String(100), nullable=False, unique=True, index=True)  # 模板代码
    category_id = Column(Integer, ForeignKey('prompt_template_categories.id'), nullable=True, index=True)

    # 提示词内容（JSON格式存储）
    prompts = Column(JSON, nullable=False)
    # 示例结构：
    # {
    #   "analysis": {
    #     "system": "你是一个...",
    #     "user_template": "请分析以下...",
    #     "variables": ["company_name", "company_desc", "uploaded_text"]
    #   },
    #   "article_generation": {
    #     "system": "你是一个...",
    #     "user_template": "基于以下分析...",
    #     "variables": ["company_name", "analysis", "angle"]
    #   }
    # }

    # 模板元数据
    industry_tags = Column(JSON)  # 行业标签 ["tech", "ai", "saas"]
    platform_tags = Column(JSON)  # 平台标签 ["zhihu", "csdn"]
    keywords = Column(JSON)  # 关键词 ["人工智能", "云计算"]

    # 配置参数
    ai_config = Column(JSON)  # AI参数配置
    # {
    #   "temperature": 0.8,
    #   "max_tokens": 3000,
    #   "model": "glm-4-flash"
    # }

    # 模板状态
    version = Column(String(20), default='1.0')  # 版本号
    status = Column(String(20), default='draft', index=True)  # draft/active/archived
    is_default = Column(Boolean, default=False)  # 是否为默认模板

    # 使用统计
    usage_count = Column(Integer, default=0)  # 使用次数
    success_rate = Column(Float, default=0.0)  # 成功率
    avg_rating = Column(Float, default=0.0)  # 平均评分

    # 元信息
    description = Column(Text)  # 模板描述
    example_company = Column(String(200))  # 示例公司
    example_output = Column(Text)  # 示例输出
    notes = Column(Text)  # 备注

    # 引用的样例
    referenced_examples = Column(JSON)  # 引用的样例ID列表

    # 审计信息
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    updated_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # 关系
    category = relationship("PromptTemplateCategory", back_populates="templates")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    usage_logs = relationship("PromptTemplateUsageLog", back_populates="template", cascade="all, delete-orphan")
    audit_logs = relationship("PromptTemplateAuditLog", back_populates="template", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PromptTemplate(id={self.id}, name='{self.name}', code='{self.code}', status='{self.status}')>"

    def to_dict(self, include_prompts=True):
        """转换为字典"""
        data = {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'category_id': self.category_id,
            'industry_tags': self.industry_tags or [],
            'platform_tags': self.platform_tags or [],
            'keywords': self.keywords or [],
            'ai_config': self.ai_config or {},
            'version': self.version,
            'status': self.status,
            'is_default': self.is_default,
            'usage_count': self.usage_count,
            'success_rate': self.success_rate,
            'avg_rating': self.avg_rating,
            'description': self.description,
            'example_company': self.example_company,
            'example_output': self.example_output,
            'notes': self.notes,
            'referenced_examples': self.referenced_examples or [],
            'created_by': self.created_by,
            'updated_by': self.updated_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_prompts:
            data['prompts'] = self.prompts or {}
        return data


class PromptTemplateUsageLog(Base):
    """提示词模板使用记录表"""
    __tablename__ = 'prompt_template_usage_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(Integer, ForeignKey('prompt_templates.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    workflow_id = Column(Integer, ForeignKey('workflows.id'), nullable=True)

    # 使用方式
    selection_method = Column(String(20), index=True)  # manual/auto

    # 匹配信息（如果是自动选择）
    match_score = Column(Float)  # 匹配分数
    match_reason = Column(Text)  # 匹配原因

    # 结果信息
    status = Column(String(20), index=True)  # success/failed
    error_message = Column(Text)
    articles_generated = Column(Integer, default=0)

    # 用户反馈
    user_rating = Column(Integer)  # 1-5星评分
    user_feedback = Column(Text)

    # 时间戳
    used_at = Column(TIMESTAMP, server_default=func.now(), index=True)

    # 关系
    template = relationship("PromptTemplate", back_populates="usage_logs")
    user = relationship("User")
    workflow = relationship("Workflow")

    def __repr__(self):
        return f"<PromptTemplateUsageLog(id={self.id}, template_id={self.template_id}, status='{self.status}')>"

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'template_id': self.template_id,
            'user_id': self.user_id,
            'workflow_id': self.workflow_id,
            'selection_method': self.selection_method,
            'match_score': self.match_score,
            'match_reason': self.match_reason,
            'status': self.status,
            'error_message': self.error_message,
            'articles_generated': self.articles_generated,
            'user_rating': self.user_rating,
            'user_feedback': self.user_feedback,
            'used_at': self.used_at.isoformat() if self.used_at else None
        }


class PromptTemplateAuditLog(Base):
    """提示词模板审计日志表"""
    __tablename__ = 'prompt_template_audit_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(Integer, ForeignKey('prompt_templates.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)

    # 操作信息
    action = Column(String(50), nullable=False, index=True)  # create/update/delete/activate/archive
    action_detail = Column(Text)  # 操作详情

    # 变更内容
    changes = Column(JSON)  # 记录字段变更前后的值

    # IP和设备信息
    ip_address = Column(String(50))
    user_agent = Column(String(500))

    # 时间戳
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)

    # 关系
    template = relationship("PromptTemplate", back_populates="audit_logs")
    user = relationship("User")

    def __repr__(self):
        return f"<PromptTemplateAuditLog(id={self.id}, action='{self.action}', template_id={self.template_id})>"

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'template_id': self.template_id,
            'user_id': self.user_id,
            'action': self.action,
            'action_detail': self.action_detail,
            'changes': self.changes or {},
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class PromptExampleLibrary(Base):
    """提示词样例库表"""
    __tablename__ = 'prompt_example_library'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 基本信息
    title = Column(String(200), nullable=False, index=True)  # 样例标题
    code = Column(String(100), unique=True, nullable=False, index=True)  # 样例代码
    type = Column(String(50), nullable=False, index=True)  # 类型
    # 类型包括：
    # - industry_feature (行业特征)
    # - platform_style (平台风格)
    # - full_template (完整模板)
    # - best_practice (最佳实践)

    # 分类标签
    industry = Column(String(50), index=True)  # 所属行业：tech/finance/education等
    platform = Column(String(50), index=True)  # 所属平台：zhihu/csdn/juejin等
    stage = Column(String(50), index=True)  # 适用阶段：analysis/generation

    # 样例内容（JSON格式）
    content = Column(JSON, nullable=False)

    # 展示配置
    display_order = Column(Integer, default=0)  # 展示顺序
    is_recommended = Column(Boolean, default=False)  # 是否推荐
    tags = Column(JSON)  # 标签：["初学者友好", "高级", "热门"]

    # 统计信息
    view_count = Column(Integer, default=0)  # 查看次数
    reference_count = Column(Integer, default=0)  # 被引用次数

    # 元信息
    description = Column(Text)  # 样例描述
    author = Column(String(100))  # 作者/来源
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # 关系
    creator = relationship("User")

    def __repr__(self):
        return f"<PromptExampleLibrary(id={self.id}, title='{self.title}', type='{self.type}')>"

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'code': self.code,
            'type': self.type,
            'industry': self.industry,
            'platform': self.platform,
            'stage': self.stage,
            'content': self.content or {},
            'display_order': self.display_order,
            'is_recommended': self.is_recommended,
            'tags': self.tags or [],
            'view_count': self.view_count,
            'reference_count': self.reference_count,
            'description': self.description,
            'author': self.author,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
