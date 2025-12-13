#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：添加提示词模板相关字段
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from models import engine, SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate():
    """执行数据库迁移"""
    session = SessionLocal()

    try:
        logger.info("开始数据库迁移...")

        # 1. 在 User 表添加 role 字段
        logger.info("1. 在 User 表添加 role 字段...")
        try:
            session.execute(text("""
                ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user'
            """))
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)
            """))
            logger.info("   ✓ User.role 字段添加成功")
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                logger.info("   ○ User.role 字段已存在，跳过")
            else:
                raise

        # 2. 在 Workflow 表添加 template 相关字段
        logger.info("2. 在 Workflow 表添加模板相关字段...")
        try:
            session.execute(text("""
                ALTER TABLE workflows ADD COLUMN template_id INTEGER
            """))
            logger.info("   ✓ Workflow.template_id 字段添加成功")
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                logger.info("   ○ Workflow.template_id 字段已存在，跳过")
            else:
                raise

        try:
            session.execute(text("""
                ALTER TABLE workflows ADD COLUMN template_selection_method VARCHAR(20)
            """))
            logger.info("   ✓ Workflow.template_selection_method 字段添加成功")
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                logger.info("   ○ Workflow.template_selection_method 字段已存在，跳过")
            else:
                raise

        try:
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_workflows_template_id ON workflows(template_id)
            """))
            logger.info("   ✓ 索引创建成功")
        except Exception as e:
            logger.warning(f"   ! 索引创建警告: {e}")

        # 3. 创建新表
        logger.info("3. 创建提示词模板相关表...")

        # 导入新模型以创建表
        from models_prompt_template import (
            PromptTemplateCategory,
            PromptTemplate,
            PromptTemplateUsageLog,
            PromptTemplateAuditLog,
            PromptExampleLibrary,
            Base
        )

        # 创建所有新表
        Base.metadata.create_all(bind=engine, tables=[
            PromptTemplateCategory.__table__,
            PromptTemplate.__table__,
            PromptTemplateUsageLog.__table__,
            PromptTemplateAuditLog.__table__,
            PromptExampleLibrary.__table__
        ])

        logger.info("   ✓ 新表创建成功")

        # 提交更改
        session.commit()
        logger.info("\n数据库迁移完成！")

        # 显示新表信息
        result = session.execute(text("""
            SELECT name FROM sqlite_master
            WHERE type='table'
            AND name LIKE 'prompt%'
            ORDER BY name
        """))
        tables = [row[0] for row in result]

        logger.info(f"\n新增的表 ({len(tables)}):")
        for table in tables:
            logger.info(f"  - {table}")

        return True

    except Exception as e:
        session.rollback()
        logger.error(f"\n迁移失败: {e}", exc_info=True)
        return False

    finally:
        session.close()


if __name__ == '__main__':
    success = migrate()
    sys.exit(0 if success else 1)
