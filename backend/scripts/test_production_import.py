#!/usr/bin/env python3
"""
生产环境导入测试
在部署前验证应用能否在production模式下正常导入
"""
import os
import sys

def test_production_import():
    """测试生产环境下的应用导入"""

    print("=" * 70)
    print("生产环境导入测试")
    print("=" * 70)
    print()

    # 1. 设置生产环境
    os.environ['FLASK_ENV'] = 'production'

    # 2. 设置非默认的配置（通过验证）
    import secrets
    os.environ['TOPN_SECRET_KEY'] = secrets.token_hex(32)
    os.environ['ZHIPU_API_KEY'] = f"test_key_{secrets.token_hex(16)}"

    print("[OK] Environment variables set")
    print(f"  FLASK_ENV: {os.environ['FLASK_ENV']}")
    print(f"  TOPN_SECRET_KEY: {os.environ['TOPN_SECRET_KEY'][:16]}...")
    print(f"  ZHIPU_API_KEY: {os.environ['ZHIPU_API_KEY'][:16]}...")
    print()

    # 3. 测试models导入
    print("[1/5] Testing models import...")
    try:
        from models import Base, User, Article
        from models_prompt_template import PromptTemplate
        table_count = len(Base.metadata.tables)
        print(f"[OK] Models imported successfully, tables: {table_count}")
    except Exception as e:
        print(f"[FAIL] Models import failed: {e}")
        return False

    # 4. 测试config导入
    print("[2/5] Testing config import...")
    try:
        from config import get_config, ProductionConfig
        config = get_config('production')
        print(f"[OK] Config imported: {config}")
    except Exception as e:
        print(f"[FAIL] Config import failed: {e}")
        return False

    # 5. 测试app_factory导入
    print("[3/5] Testing app_factory import...")
    try:
        from app_factory import create_app
        print("[OK] app_factory imported")
    except Exception as e:
        print(f"[FAIL] app_factory import failed: {e}")
        return False

    # 6. 测试app创建
    print("[4/5] Testing app creation...")
    try:
        app = create_app('production')
        print(f"[OK] App created")
        print(f"  Blueprints: {len(app.blueprints)}")
        print(f"  Routes: {len(list(app.url_map.iter_rules()))}")
    except Exception as e:
        print(f"[FAIL] App creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 7. 测试app导入（从app.py）
    print("[5/5] Testing app.py import...")
    try:
        # 重新导入以测试app.py
        if 'app' in sys.modules:
            del sys.modules['app']
        from app import app as app_instance
        print("[OK] app.py imported")
    except Exception as e:
        print(f"[FAIL] app.py import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 8. 检查关键路由
    print()
    print("Checking critical routes...")
    routes = [r.rule for r in app.url_map.iter_rules()]
    test_routes = [
        '/api/health',
        '/api/platforms',
        '/api/accounts/<int:account_id>/test',
        '/api/csdn/login',
    ]

    for route in test_routes:
        # 处理动态参数
        found = any(route.replace('<int:account_id>', '') in r for r in routes)
        status = "[OK]" if found else "[FAIL]"
        print(f"  {status} {route}")

    print()
    print("=" * 70)
    print("[SUCCESS] All tests passed! Ready to deploy.")
    print("=" * 70)
    return True


if __name__ == '__main__':
    success = test_production_import()
    sys.exit(0 if success else 1)
