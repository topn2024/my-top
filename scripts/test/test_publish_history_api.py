#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试发布历史API端点
"""
import sys
import os
import io

# 设置控制台编码为UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

def test_imports():
    """测试导入"""
    print("测试导入模块...")
    try:
        from models import PublishHistory, Article, User, get_db_session
        print("✓ 成功导入 models")

        from services.publish_service import PublishService
        print("✓ 成功导入 PublishService")

        from config import get_config
        print("✓ 成功导入 config")

        return True
    except Exception as e:
        print(f"✗ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_connection():
    """测试数据库连接"""
    print("\n测试数据库连接...")
    try:
        from models import get_db_session, PublishHistory

        db = get_db_session()
        # 尝试查询发布历史表
        count = db.query(PublishHistory).count()
        print(f"✓ 数据库连接成功，发布历史记录数: {count}")
        db.close()
        return True
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_publish_service():
    """测试发布服务"""
    print("\n测试发布服务...")
    try:
        from services.publish_service import PublishService
        from config import get_config

        config = get_config()
        service = PublishService(config)

        print("✓ PublishService 实例化成功")

        # 测试获取发布历史（使用一个可能存在的用户ID）
        history = service.get_publish_history(user_id=1, limit=5)
        print(f"✓ 获取发布历史成功，记录数: {len(history)}")

        if history:
            print("\n最近的发布记录:")
            for h in history[:3]:
                print(f"  - ID: {h['id']}, 平台: {h['platform']}, 状态: {h['status']}")
                if 'article_title' in h:
                    print(f"    文章标题: {h['article_title']}")
                print(f"    发布时间: {h['published_at']}")
        else:
            print("  暂无发布记录")

        return True
    except Exception as e:
        print(f"✗ 测试发布服务失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_endpoints():
    """测试API端点"""
    print("\n测试API端点...")
    try:
        from app_factory import create_app

        app = create_app('testing')
        client = app.test_client()

        # 测试健康检查
        response = client.get('/api/health')
        print(f"✓ GET /api/health - Status: {response.status_code}")

        # 注意: 测试发布历史端点需要登录认证
        # 这里只测试端点是否存在（未授权应该返回401）
        response = client.get('/api/publish_history')
        if response.status_code == 401:
            print(f"✓ GET /api/publish_history - 需要认证 (Status: {response.status_code})")
        elif response.status_code == 200:
            print(f"✓ GET /api/publish_history - Status: {response.status_code}")
        else:
            print(f"⚠ GET /api/publish_history - Status: {response.status_code}")

        return True
    except Exception as e:
        print(f"✗ 测试API端点失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("="*60)
    print("发布历史API测试")
    print("="*60)

    results = []

    # 运行所有测试
    results.append(("导入测试", test_imports()))
    results.append(("数据库连接测试", test_database_connection()))
    results.append(("发布服务测试", test_publish_service()))
    results.append(("API端点测试", test_api_endpoints()))

    # 输出结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)

    for name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{name}: {status}")

    # 总结
    total = len(results)
    passed = sum(1 for _, success in results if success)
    print(f"\n总计: {passed}/{total} 测试通过")

    return all(success for _, success in results)


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
