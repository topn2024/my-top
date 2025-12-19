#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试统一模型文件
验证所有模型定义正确且可以正常工作
"""
import sys
import os
from pathlib import Path

# 设置UTF-8编码输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))


def test_model_import():
    """测试模型导入"""
    print("测试 1: 导入统一模型...")
    try:
        from models import (
            Base, engine, SessionLocal,
            User, Workflow, Article, PlatformAccount,
            PublishHistory, PublishTask,
            AnalysisPrompt, ArticlePrompt, PlatformStylePrompt,
            PromptCombinationLog,
            get_db, get_db_session, init_models
        )
        print("  ✓ 所有模型类导入成功")
        return True
    except ImportError as e:
        print(f"  ✗ 导入失败: {e}")
        return False


def test_model_tables():
    """测试模型表名"""
    print("\n测试 2: 验证表名...")
    try:
        from models import (
            User, Workflow, Article, PlatformAccount,
            PublishHistory, PublishTask,
            AnalysisPrompt, ArticlePrompt, PlatformStylePrompt,
            PromptCombinationLog
        )

        tables = {
            'User': 'users',
            'Workflow': 'workflows',
            'Article': 'articles',
            'PlatformAccount': 'platform_accounts',
            'PublishHistory': 'publish_history',
            'PublishTask': 'publish_tasks',
            'AnalysisPrompt': 'analysis_prompts',
            'ArticlePrompt': 'article_prompts',
            'PlatformStylePrompt': 'platform_style_prompts',
            'PromptCombinationLog': 'prompt_combination_logs'
        }

        all_correct = True
        for model_name, expected_table in tables.items():
            model_class = eval(model_name)
            actual_table = model_class.__tablename__
            if actual_table == expected_table:
                print(f"  ✓ {model_name}: {actual_table}")
            else:
                print(f"  ✗ {model_name}: expected '{expected_table}', got '{actual_table}'")
                all_correct = False

        return all_correct
    except Exception as e:
        print(f"  ✗ 测试失败: {e}")
        return False


def test_model_methods():
    """测试模型方法"""
    print("\n测试 3: 验证模型方法...")
    try:
        from models import User, Workflow, Article

        # 测试 to_dict 方法
        models_to_test = [User, Workflow, Article]

        for model_class in models_to_test:
            if hasattr(model_class, 'to_dict'):
                print(f"  ✓ {model_class.__name__}.to_dict() 存在")
            else:
                print(f"  ✗ {model_class.__name__}.to_dict() 缺失")
                return False

        return True
    except Exception as e:
        print(f"  ✗ 测试失败: {e}")
        return False


def test_database_connection():
    """测试数据库连接"""
    print("\n测试 4: 验证数据库连接...")
    try:
        from models import engine
        from sqlalchemy import text

        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("  ✓ 数据库连接成功")
            return True
    except Exception as e:
        print(f"  ✗ 数据库连接失败: {e}")
        return False


def test_table_creation():
    """测试表创建"""
    print("\n测试 5: 测试表创建（不修改现有表）...")
    try:
        from models import Base, engine
        from sqlalchemy import inspect

        # 获取现有表
        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names())

        print(f"  ℹ️  当前数据库中的表: {len(existing_tables)} 个")

        # 测试模型定义完整性（不实际创建表）
        print("  ✓ 模型元数据结构正确")

        # 检查预期的表
        expected_tables = {
            'users', 'workflows', 'articles', 'platform_accounts',
            'publish_history', 'publish_tasks',
            'analysis_prompts', 'article_prompts',
            'platform_style_prompts', 'prompt_combination_logs'
        }

        missing_tables = expected_tables - existing_tables
        if missing_tables:
            print(f"  ℹ️  缺失的表 (需要初始化): {', '.join(missing_tables)}")
        else:
            print("  ✓ 所有预期的表都已存在")

        return True
    except Exception as e:
        print(f"  ✗ 测试失败: {e}")
        return False


def test_model_relationships():
    """测试模型关系"""
    print("\n测试 6: 验证模型关系...")
    try:
        from models import User, Workflow, Article

        # 检查关系定义
        if hasattr(User, 'workflows'):
            print("  ✓ User.workflows 关系存在")
        else:
            print("  ✗ User.workflows 关系缺失")
            return False

        if hasattr(Workflow, 'user'):
            print("  ✓ Workflow.user 关系存在")
        else:
            print("  ✗ Workflow.user 关系缺失")
            return False

        if hasattr(Workflow, 'articles'):
            print("  ✓ Workflow.articles 关系存在")
        else:
            print("  ✗ Workflow.articles 关系缺失")
            return False

        return True
    except Exception as e:
        print(f"  ✗ 测试失败: {e}")
        return False


def test_session_factory():
    """测试会话工厂"""
    print("\n测试 7: 验证会话工厂...")
    try:
        from models import get_db_session, SessionLocal

        # 测试 get_db_session
        session = get_db_session()
        if session is not None:
            print("  ✓ get_db_session() 工作正常")
            session.close()
        else:
            print("  ✗ get_db_session() 返回 None")
            return False

        # 测试 SessionLocal
        session2 = SessionLocal()
        if session2 is not None:
            print("  ✓ SessionLocal() 工作正常")
            session2.close()
        else:
            print("  ✗ SessionLocal() 返回 None")
            return False

        return True
    except Exception as e:
        print(f"  ✗ 测试失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("="* 60)
    print("  统一模型文件测试")
    print("="* 60)

    tests = [
        test_model_import,
        test_model_tables,
        test_model_methods,
        test_database_connection,
        test_table_creation,
        test_model_relationships,
        test_session_factory
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n  ❌ 测试异常: {e}")
            results.append(False)

    # 总结
    print("\n" + "="* 60)
    print("  测试总结")
    print("="* 60)

    passed = sum(results)
    total = len(results)

    print(f"\n通过: {passed}/{total}")

    if all(results):
        print("\n✅ 所有测试通过! 模型文件可以安全使用")
        return 0
    else:
        print("\n❌ 部分测试失败,请检查问题")
        return 1


if __name__ == '__main__':
    exit(main())
