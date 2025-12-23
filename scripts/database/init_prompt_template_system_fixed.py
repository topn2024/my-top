#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提示词模板系统初始化脚本 - 修复版
完整初始化数据库和预置数据
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from models import Base, engine, SessionLocal
from models_prompt_template import (
    PromptTemplateCategory,
    PromptTemplate,
    PromptTemplateUsageLog,
    PromptTemplateAuditLog,
    PromptExampleLibrary
)
import logging
from werkzeug.security import generate_password_hash

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def init_database():
    """初始化数据库"""
    logger.info("="*60)
    logger.info("Prompt Template System - Database Initialization")
    logger.info("="*60)

    try:
        # 1. 创建所有基础表
        logger.info("\n[1/6] Creating base tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("   [OK] Base tables created")

        # 2. 添加新字段到现有表
        logger.info("\n[2/6] Adding new fields to existing tables...")
        session = SessionLocal()

        try:
            # 添加 User.role 字段
            try:
                session.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user'"))
                session.commit()
                logger.info("   [OK] User.role field added")
            except Exception as e:
                if "duplicate" in str(e).lower() or "already exists" in str(e).lower():
                    logger.info("   [SKIP] User.role field exists")
                else:
                    raise

            # 添加 Workflow 模板相关字段
            try:
                session.execute(text("ALTER TABLE workflows ADD COLUMN template_id INTEGER"))
                session.execute(text("ALTER TABLE workflows ADD COLUMN template_selection_method VARCHAR(20)"))
                session.commit()
                logger.info("   [OK] Workflow template fields added")
            except Exception as e:
                if "duplicate" in str(e).lower() or "already exists" in str(e).lower():
                    logger.info("   [SKIP] Workflow template fields exist")
                else:
                    raise

        finally:
            session.close()

        logger.info("   [OK] Field migration completed")

        return True

    except Exception as e:
        logger.error(f"\n[ERROR] Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_admin_user():
    """创建管理员用户 - 使用SQL"""
    logger.info("\n[3/6] Creating admin user...")
    session = SessionLocal()

    try:
        # 检查是否已存在管理员
        result = session.execute(text("SELECT id FROM users WHERE username = 'admin'"))
        admin_exists = result.fetchone()

        if admin_exists:
            # 更新现有管理员角色
            session.execute(text("UPDATE users SET role = 'admin' WHERE username = 'admin'"))
            session.commit()
            logger.info("   [OK] Admin user exists, role updated")
        else:
            # 创建新管理员
            password_hash = generate_password_hash('TopN@2024')
            session.execute(text("""
                INSERT INTO users (username, email, password_hash, full_name, role, is_active)
                VALUES ('admin', 'admin@topn.com', :password_hash, 'System Administrator', 'admin', 1)
            """), {'password_hash': password_hash})
            session.commit()
            logger.info("   [OK] Admin user created")
            logger.info("        Username: admin")
            logger.info("        Password: TopN@2024")

        return True

    except Exception as e:
        session.rollback()
        logger.error(f"   [ERROR] Creating admin failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        session.close()


def init_categories():
    """初始化模板分类"""
    logger.info("\n[4/6] Initializing template categories...")
    session = SessionLocal()

    categories = [
        # 顶层分类
        {'name': 'Industry', 'code': 'industry', 'parent_code': None, 'description': 'Industry-based template categories'},
        {'name': 'Platform', 'code': 'platform', 'parent_code': None, 'description': 'Platform-based template categories'},
        {'name': 'Purpose', 'code': 'purpose', 'parent_code': None, 'description': 'Purpose-based template categories'},

        # 行业子分类
        {'name': 'Technology', 'code': 'tech', 'parent_code': 'industry'},
        {'name': 'Finance', 'code': 'finance', 'parent_code': 'industry'},
        {'name': 'Education', 'code': 'education', 'parent_code': 'industry'},
        {'name': 'Healthcare', 'code': 'healthcare', 'parent_code': 'industry'},
        {'name': 'E-commerce', 'code': 'ecommerce', 'parent_code': 'industry'},

        # 平台子分类
        {'name': 'Zhihu', 'code': 'zhihu', 'parent_code': 'platform'},
        {'name': 'CSDN', 'code': 'csdn', 'parent_code': 'platform'},
        {'name': 'Juejin', 'code': 'juejin', 'parent_code': 'platform'},

        # 目的子分类
        {'name': 'Brand Marketing', 'code': 'brand', 'parent_code': 'purpose'},
        {'name': 'Product Promotion', 'code': 'product', 'parent_code': 'purpose'},
        {'name': 'Tech Sharing', 'code': 'tech_share', 'parent_code': 'purpose'},
    ]

    try:
        created_count = 0
        parent_map = {}

        # 先创建顶层分类
        for cat_data in categories:
            if cat_data['parent_code'] is None:
                existing = session.query(PromptTemplateCategory).filter_by(code=cat_data['code']).first()
                if not existing:
                    cat = PromptTemplateCategory(
                        name=cat_data['name'],
                        code=cat_data['code'],
                        description=cat_data.get('description', ''),
                        parent_id=None,
                        sort_order=0
                    )
                    session.add(cat)
                    session.flush()
                    parent_map[cat_data['code']] = cat.id
                    created_count += 1
                else:
                    parent_map[cat_data['code']] = existing.id

        # 再创建子分类
        for cat_data in categories:
            if cat_data['parent_code'] is not None:
                existing = session.query(PromptTemplateCategory).filter_by(code=cat_data['code']).first()
                if not existing:
                    parent_id = parent_map.get(cat_data['parent_code'])
                    cat = PromptTemplateCategory(
                        name=cat_data['name'],
                        code=cat_data['code'],
                        description=cat_data.get('description', ''),
                        parent_id=parent_id,
                        sort_order=0
                    )
                    session.add(cat)
                    created_count += 1

        session.commit()
        logger.info(f"   [OK] Created {created_count} categories")

        return True

    except Exception as e:
        session.rollback()
        logger.error(f"   [ERROR] Initializing categories failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        session.close()


def init_example_library():
    """初始化样例库"""
    logger.info("\n[5/6] Initializing example library...")
    session = SessionLocal()

    examples = [
        # 行业特征样例 - 科技
        {
            'title': 'Tech Industry Features',
            'code': 'industry_tech_features',
            'type': 'industry_feature',
            'industry': 'tech',
            'platform': None,
            'stage': None,
            'description': 'Analysis dimensions, keywords, and prompt examples for tech industry',
            'is_recommended': True,
            'tags': ['recommended', 'beginner-friendly'],
            'content': {
                'industry': 'tech',
                'features': {
                    'analysis_dimensions': [
                        'Technical Innovation',
                        'R&D Investment and Patents',
                        'Product Architecture',
                        'Industry Position',
                        'Future Tech Roadmap'
                    ],
                    'focus_points': [
                        'Core Tech Stack',
                        'Technical Barriers',
                        'Innovation Breakthroughs',
                        'Team Capability',
                        'Open Source Contributions'
                    ],
                    'keywords': [
                        'Cloud Computing', 'AI', 'Big Data', 'IoT', '5G',
                        'Blockchain', 'Edge Computing', 'Containers', 'Microservices', 'DevOps'
                    ],
                    'tone': 'Professional, tech-oriented, data-driven',
                    'avoid': ['Over-hyping', 'Lacking technical details', 'Vague concepts']
                }
            }
        },

        # 平台风格样例 - 知乎
        {
            'title': 'Zhihu Platform Style Guide',
            'code': 'platform_zhihu_style',
            'type': 'platform_style',
            'industry': None,
            'platform': 'zhihu',
            'stage': None,
            'description': 'Writing requirements, style characteristics, and best practices for Zhihu',
            'is_recommended': True,
            'tags': ['recommended', 'popular'],
            'content': {
                'platform': 'zhihu',
                'style_guide': {
                    'tone': 'Professional yet approachable, objective and rational',
                    'perspective': 'First-person or third-person objective',
                    'structure': [
                        'Question introduction',
                        'Background context',
                        'In-depth analysis',
                        'Case studies',
                        'Conclusion'
                    ],
                    'length': '1500-3000 words ideal',
                    'format': {
                        'paragraphs': 'Clear paragraphs, 3-5 lines each',
                        'headings': 'Use subheadings appropriately',
                        'lists': 'Use lists for readability',
                        'emphasis': 'Bold key points moderately'
                    }
                }
            }
        }
    ]

    try:
        created_count = 0

        for example_data in examples:
            existing = session.query(PromptExampleLibrary).filter_by(code=example_data['code']).first()
            if not existing:
                example = PromptExampleLibrary(
                    title=example_data['title'],
                    code=example_data['code'],
                    type=example_data['type'],
                    industry=example_data.get('industry'),
                    platform=example_data.get('platform'),
                    stage=example_data.get('stage'),
                    content=example_data['content'],
                    description=example_data.get('description'),
                    is_recommended=example_data.get('is_recommended', False),
                    tags=example_data.get('tags', []),
                    author='System',
                    display_order=0
                )
                session.add(example)
                created_count += 1

        session.commit()
        logger.info(f"   [OK] Created {created_count} examples")

        return True

    except Exception as e:
        session.rollback()
        logger.error(f"   [ERROR] Initializing example library failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        session.close()


def verify_installation():
    """验证安装"""
    logger.info("\n[6/6] Verifying installation...")
    session = SessionLocal()

    try:
        # 统计数据
        result = session.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.scalar()

        result = session.execute(text("SELECT COUNT(*) FROM users WHERE role = 'admin'"))
        admin_count = result.scalar()

        category_count = session.query(PromptTemplateCategory).count()
        example_count = session.query(PromptExampleLibrary).count()

        logger.info(f"   [OK] Users: {user_count} (Admins: {admin_count})")
        logger.info(f"   [OK] Template Categories: {category_count}")
        logger.info(f"   [OK] Example Library: {example_count}")

        logger.info("\n" + "="*60)
        logger.info("Installation Complete!")
        logger.info("="*60)
        logger.info("\nPrompt Template System initialized successfully:")
        logger.info("  - 5 new database tables")
        logger.info(f"  - {category_count} template categories")
        logger.info(f"  - {example_count} example templates")
        logger.info("  - 1 admin account (admin / TopN@2024)")
        logger.info("\nNext steps:")
        logger.info("  1. Start application: python app_factory.py")
        logger.info("  2. Access admin panel to create templates")
        logger.info("  3. Users can use templates to generate articles")
        logger.info("")

        return True

    except Exception as e:
        logger.error(f"   [ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        session.close()


def main():
    """主函数"""
    steps = [
        init_database,
        create_admin_user,
        init_categories,
        init_example_library,
        verify_installation
    ]

    for step in steps:
        if not step():
            logger.error("\nInitialization failed!")
            return False

    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
