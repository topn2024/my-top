#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建三模块提示词系统数据库表
"""
import sys
import os
# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from models import SessionLocal, engine

def create_tables():
    """创建新的提示词系统表"""
    session = SessionLocal()

    try:
        print('开始创建三模块提示词系统表...')

        # 1. 创建 analysis_prompts 表
        print('1. 创建 analysis_prompts 表...')
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS analysis_prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(200) NOT NULL,
                code VARCHAR(100) UNIQUE NOT NULL,
                description TEXT,
                system_prompt TEXT NOT NULL,
                user_template TEXT NOT NULL,
                variables TEXT,
                temperature REAL DEFAULT 0.7,
                max_tokens INTEGER DEFAULT 2000,
                model VARCHAR(50) DEFAULT 'glm-4-flash',
                category_id INTEGER,
                industry_tags TEXT,
                keywords TEXT,
                status VARCHAR(20) DEFAULT 'draft',
                version VARCHAR(20) DEFAULT '1.0',
                is_default INTEGER DEFAULT 0,
                usage_count INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                avg_rating REAL DEFAULT 0.0,
                example_company VARCHAR(200),
                example_output TEXT,
                notes TEXT,
                created_by INTEGER,
                updated_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # 创建索引
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_analysis_prompts_code
            ON analysis_prompts(code)
        """))
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_analysis_prompts_status
            ON analysis_prompts(status)
        """))

        # 2. 创建 article_prompts 表
        print('2. 创建 article_prompts 表...')
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS article_prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(200) NOT NULL,
                code VARCHAR(100) UNIQUE NOT NULL,
                description TEXT,
                system_prompt TEXT NOT NULL,
                user_template TEXT NOT NULL,
                variables TEXT,
                default_angles TEXT,
                article_structure TEXT,
                temperature REAL DEFAULT 0.8,
                max_tokens INTEGER DEFAULT 3000,
                model VARCHAR(50) DEFAULT 'glm-4-flash',
                category_id INTEGER,
                industry_tags TEXT,
                style_tags TEXT,
                keywords TEXT,
                status VARCHAR(20) DEFAULT 'draft',
                version VARCHAR(20) DEFAULT '1.0',
                is_default INTEGER DEFAULT 0,
                usage_count INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                avg_rating REAL DEFAULT 0.0,
                example_input TEXT,
                example_output TEXT,
                notes TEXT,
                created_by INTEGER,
                updated_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # 创建索引
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_article_prompts_code
            ON article_prompts(code)
        """))
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_article_prompts_status
            ON article_prompts(status)
        """))

        # 3. 创建 platform_style_prompts 表
        print('3. 创建 platform_style_prompts 表...')
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS platform_style_prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(200) NOT NULL,
                code VARCHAR(100) UNIQUE NOT NULL,
                description TEXT,
                platform VARCHAR(50) NOT NULL,
                platform_display_name VARCHAR(100),
                system_prompt TEXT NOT NULL,
                user_template TEXT NOT NULL,
                variables TEXT,
                style_features TEXT,
                formatting_rules TEXT,
                temperature REAL DEFAULT 0.7,
                max_tokens INTEGER DEFAULT 3000,
                model VARCHAR(50) DEFAULT 'glm-4-flash',
                apply_stage VARCHAR(20) DEFAULT 'both',
                status VARCHAR(20) DEFAULT 'draft',
                version VARCHAR(20) DEFAULT '1.0',
                is_default INTEGER DEFAULT 0,
                usage_count INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                avg_rating REAL DEFAULT 0.0,
                example_before TEXT,
                example_after TEXT,
                notes TEXT,
                created_by INTEGER,
                updated_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # 创建索引
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_platform_style_prompts_code
            ON platform_style_prompts(code)
        """))
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_platform_style_prompts_platform
            ON platform_style_prompts(platform)
        """))
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_platform_style_prompts_status
            ON platform_style_prompts(status)
        """))

        # 4. 创建 prompt_combination_logs 表
        print('4. 创建 prompt_combination_logs 表...')
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS prompt_combination_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                workflow_id INTEGER,
                analysis_prompt_id INTEGER,
                article_prompt_id INTEGER,
                platform_style_prompt_id INTEGER,
                selection_method VARCHAR(20),
                applied_at_generation INTEGER DEFAULT 0,
                applied_at_publish INTEGER DEFAULT 0,
                status VARCHAR(20),
                articles_generated INTEGER DEFAULT 0,
                articles_published INTEGER DEFAULT 0,
                error_message TEXT,
                user_rating INTEGER,
                user_feedback TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # 创建索引
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_prompt_combination_logs_user_id
            ON prompt_combination_logs(user_id)
        """))
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_prompt_combination_logs_workflow_id
            ON prompt_combination_logs(workflow_id)
        """))

        session.commit()
        print('[OK] 所有表创建成功')

        # 5. 修改 workflows 表（添加新字段）
        print('5. 修改 workflows 表...')
        try:
            # 检查字段是否已存在
            result = session.execute(text("PRAGMA table_info(workflows)"))
            columns = [row[1] for row in result]

            if 'analysis_prompt_id' not in columns:
                session.execute(text("ALTER TABLE workflows ADD COLUMN analysis_prompt_id INTEGER"))
                print('[OK] 添加 analysis_prompt_id 字段')

            if 'article_prompt_id' not in columns:
                session.execute(text("ALTER TABLE workflows ADD COLUMN article_prompt_id INTEGER"))
                print('[OK] 添加 article_prompt_id 字段')

            if 'platform_style_prompt_id' not in columns:
                session.execute(text("ALTER TABLE workflows ADD COLUMN platform_style_prompt_id INTEGER"))
                print('[OK] 添加 platform_style_prompt_id 字段')

            session.commit()
        except Exception as e:
            print(f'[WARN] 修改 workflows 表时出错（可能字段已存在）: {e}')

        # 6. 修改 articles 表（添加新字段）
        print('6. 修改 articles 表...')
        try:
            result = session.execute(text("PRAGMA table_info(articles)"))
            columns = [row[1] for row in result]

            if 'original_content' not in columns:
                session.execute(text("ALTER TABLE articles ADD COLUMN original_content TEXT"))
                print('[OK] 添加 original_content 字段')

            if 'platform_style_id' not in columns:
                session.execute(text("ALTER TABLE articles ADD COLUMN platform_style_id INTEGER"))
                print('[OK] 添加 platform_style_id 字段')

            if 'style_converted_at' not in columns:
                session.execute(text("ALTER TABLE articles ADD COLUMN style_converted_at TIMESTAMP"))
                print('[OK] 添加 style_converted_at 字段')

            session.commit()
        except Exception as e:
            print(f'[WARN] 修改 articles 表时出错（可能字段已存在）: {e}')

        print('\n[SUCCESS] 数据库迁移完成')
        return True

    except Exception as e:
        session.rollback()
        print(f'\n[ERROR] 迁移失败: {e}')
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


if __name__ == '__main__':
    print('=' * 60)
    print('三模块提示词系统 - 数据库迁移')
    print('=' * 60)
    print()

    success = create_tables()

    if success:
        print('\n[OK] 迁移成功！可以继续执行 init_prompt_v2_data.py 初始化数据')
    else:
        print('\n[ERROR] 迁移失败，请检查错误信息')

    print('=' * 60)
