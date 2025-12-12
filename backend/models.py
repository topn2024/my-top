#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLAlchemy ORM 模型定义
"""
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, TIMESTAMP, ForeignKey, JSON, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime

# 数据库连接配置
import os
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


class User(Base):
    """用户表"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
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
    article_id = Column(Integer, ForeignKey('articles.id', ondelete='CASCADE'), nullable=True, index=True)  # 允许NULL，支持临时发布
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    platform = Column(String(50), nullable=False, index=True)
    status = Column(String(50), nullable=False)
    url = Column(Text)
    message = Column(Text)
    published_at = Column(TIMESTAMP, server_default=func.now(), index=True)

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


# 辅助函数

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
    """初始化模型（创建所有表）"""
    Base.metadata.create_all(bind=engine)
    print("✓ 所有模型已初始化")


if __name__ == '__main__':
    # 测试数据库连接
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✓ 数据库连接成功")
            print(f"✓ 数据库 URL: {DATABASE_URL.replace('TopN@MySQL2024', '****')}")
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
