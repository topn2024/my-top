#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一的 SQLAlchemy ORM 模型定义
整合了核心业务模型和提示词系统模型
"""
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, TIMESTAMP, ForeignKey, JSON, Float, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import json
import os

# 数据库连接配置
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'topn.db')

# 确保数据目录存在
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

DATABASE_URL = f'sqlite:///{DB_PATH}'

# 创建引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={'check_same_thread': False},  # SQLite特定配置
    echo=False  # 生产环境设为 False
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()


# ============================================================================
# 核心业务模型
# ============================================================================

class User(Base):
    """用户表"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(String(20), default='user', nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    last_login = Column(TIMESTAMP, nullable=True)
    is_active = Column(Boolean, default=True)

    # 关系
    workflows = relationship("Workflow", back_populates="user", cascade="all, delete-orphan")
    platform_accounts = relationship("PlatformAccount", back_populates="user", cascade="all, delete-orphan")
    publish_history = relationship("PublishHistory", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active
        }


class Workflow(Base):
    """工作流表"""
    __tablename__ = 'workflows'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    company_name = Column(String(200), nullable=False)
    company_desc = Column(Text)
    uploaded_text = Column(Text)
    uploaded_filename = Column(String(255))
    template_id = Column(String(100), nullable=True)  # 使用的提示词模板ID
    analysis = Column(Text)
    article_count = Column(Integer, default=3)
    platforms = Column(JSON)  # 存储平台列表
    current_step = Column(Integer, default=1)
    status = Column(String(50), default='in_progress', index=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # 关系
    user = relationship("User", back_populates="workflows")
    articles = relationship("Article", back_populates="workflow", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Workflow(id={self.id}, company_name='{self.company_name}', status='{self.status}')>"

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'company_name': self.company_name,
            'company_desc': self.company_desc,
            'uploaded_text': self.uploaded_text,
            'uploaded_filename': self.uploaded_filename,
            'template_id': self.template_id,
            'analysis': self.analysis,
            'article_count': self.article_count,
            'platforms': self.platforms,
            'current_step': self.current_step,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Article(Base):
    """文章表"""
    __tablename__ = 'articles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_id = Column(Integer, ForeignKey('workflows.id', ondelete='CASCADE'), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    article_type = Column(String(50))
    article_order = Column(Integer, default=0, index=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # 关系
    workflow = relationship("Workflow", back_populates="articles")
    publish_history = relationship("PublishHistory", back_populates="article", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Article(id={self.id}, title='{self.title}', workflow_id={self.workflow_id})>"

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'workflow_id': self.workflow_id,
            'title': self.title,
            'content': self.content,
            'article_type': self.article_type,
            'article_order': self.article_order,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class PlatformAccount(Base):
    """平台账号表"""
    __tablename__ = 'platform_accounts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    platform = Column(String(50), nullable=False, index=True)
    username = Column(String(100), nullable=False)
    password_encrypted = Column(Text, nullable=False)
    notes = Column(Text)
    status = Column(String(50), default='active')
    last_tested = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # 关系
    user = relationship("User", back_populates="platform_accounts")

    def __repr__(self):
        return f"<PlatformAccount(id={self.id}, platform='{self.platform}', username='{self.username}')>"

    def to_dict(self, include_password=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'platform': self.platform,
            'username': self.username,
            'notes': self.notes,
            'status': self.status,
            'last_tested': self.last_tested.isoformat() if self.last_tested else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_password:
            data['password_encrypted'] = self.password_encrypted
        return data


class PublishHistory(Base):
    """发布历史表"""
    __tablename__ = 'publish_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(Integer, ForeignKey('articles.id', ondelete='CASCADE'), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    platform = Column(String(50), nullable=False, index=True)
    status = Column(String(50), nullable=False)
    url = Column(Text)
    message = Column(Text)
    published_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    article_title = Column(String(500), nullable=True)
    article_content = Column(Text, nullable=True)

    # 关系
    article = relationship("Article", back_populates="publish_history")
    user = relationship("User", back_populates="publish_history")

    def __repr__(self):
        return f"<PublishHistory(id={self.id}, platform='{self.platform}', status='{self.status}')>"

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'article_id': self.article_id,
            'article_title': self.article_title,
            'article_content': self.article_content,
            'user_id': self.user_id,
            'platform': self.platform,
            'status': self.status,
            'url': self.url,
            'message': self.message,
            'published_at': self.published_at.isoformat() if self.published_at else None
        }


class PublishTask(Base):
    """发布任务表（RQ队列任务）"""
    __tablename__ = 'publish_tasks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(100), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    article_id = Column(Integer, nullable=True)
    article_title = Column(String(500), nullable=True)
    article_content = Column(Text, nullable=True)
    platform = Column(String(50), nullable=False, index=True)
    status = Column(String(20), default='pending', index=True)
    progress = Column(Integer, default=0)
    result_url = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    started_at = Column(TIMESTAMP, nullable=True)
    completed_at = Column(TIMESTAMP, nullable=True)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<PublishTask(id={self.id}, task_id='{self.task_id}', status='{self.status}')>"

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'user_id': self.user_id,
            'article_id': self.article_id,
            'article_title': self.article_title,
            'platform': self.platform,
            'status': self.status,
            'progress': self.progress,
            'result_url': self.result_url,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# ============================================================================
# 提示词系统模型
# ============================================================================

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
    platform = Column(String(50), nullable=False, index=True)
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


# ============================================================================
# 辅助函数
# ============================================================================

def get_db():
    """获取数据库会话（用于依赖注入）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session():
    """直接获取数据库会话（用于脚本）"""
    return SessionLocal()


def init_models():
    """初始化所有模型（创建所有表）"""
    Base.metadata.create_all(bind=engine)
    print("✓ 所有数据库模型已初始化")

    # 打印创建的表列表
    print("✓ 创建的数据库表:")
    for table_name in Base.metadata.tables.keys():
        print(f"  - {table_name}")


if __name__ == '__main__':
    # 测试数据库连接
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✓ 数据库连接成功")
            print(f"✓ 数据库路径: {DB_PATH}")

        # 初始化模型
        init_models()

    except Exception as e:
        print(f"✗ 数据库操作失败: {e}")
