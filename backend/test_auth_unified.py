#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试统一认证模块
验证所有认证功能正常工作
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


def test_imports():
    """测试模块导入"""
    print("测试 1: 导入统一认证模块...")
    try:
        from auth import (
            ROLE_GUEST, ROLE_USER, ROLE_ADMIN,
            hash_password, verify_password,
            create_user, authenticate_user, get_current_user, get_user_role, is_admin,
            create_session, destroy_session,
            login_required, admin_required, role_required,
            check_page_permission, init_auth,
            PAGE_PERMISSIONS
        )
        print("  ✓ 所有导入成功")
        return True
    except ImportError as e:
        print(f"  ✗ 导入失败: {e}")
        return False


def test_password_functions():
    """测试密码功能"""
    print("\n测试 2: 密码哈希和验证...")
    try:
        from auth import hash_password, verify_password

        # 测试密码哈希
        password = "TestPassword123!"
        hashed = hash_password(password)

        if not hashed:
            print("  ✗ 密码哈希失败")
            return False

        print(f"  ✓ 密码哈希成功")

        # 测试密码验证（正确密码）
        if verify_password(hashed, password):
            print("  ✓ 正确密码验证成功")
        else:
            print("  ✗ 正确密码验证失败")
            return False

        # 测试密码验证（错误密码）
        if not verify_password(hashed, "WrongPassword"):
            print("  ✓ 错误密码验证正确拒绝")
        else:
            print("  ✗ 错误密码验证未拒绝")
            return False

        return True
    except Exception as e:
        print(f"  ✗ 测试失败: {e}")
        return False


def test_role_constants():
    """测试角色常量"""
    print("\n测试 3: 角色常量定义...")
    try:
        from auth import ROLE_GUEST, ROLE_USER, ROLE_ADMIN

        if ROLE_GUEST == 'guest':
            print("  ✓ ROLE_GUEST = 'guest'")
        else:
            print(f"  ✗ ROLE_GUEST 错误: {ROLE_GUEST}")
            return False

        if ROLE_USER == 'user':
            print("  ✓ ROLE_USER = 'user'")
        else:
            print(f"  ✗ ROLE_USER 错误: {ROLE_USER}")
            return False

        if ROLE_ADMIN == 'admin':
            print("  ✓ ROLE_ADMIN = 'admin'")
        else:
            print(f"  ✗ ROLE_ADMIN 错误: {ROLE_ADMIN}")
            return False

        return True
    except Exception as e:
        print(f"  ✗ 测试失败: {e}")
        return False


def test_decorators_exist():
    """测试装饰器定义"""
    print("\n测试 4: 装饰器定义...")
    try:
        from auth import login_required, admin_required, role_required
        import inspect

        if callable(login_required):
            print("  ✓ login_required 装饰器存在")
        else:
            print("  ✗ login_required 不是可调用对象")
            return False

        if callable(admin_required):
            print("  ✓ admin_required 装饰器存在")
        else:
            print("  ✗ admin_required 不是可调用对象")
            return False

        if callable(role_required):
            print("  ✓ role_required 装饰器存在")
        else:
            print("  ✗ role_required 不是可调用对象")
            return False

        return True
    except Exception as e:
        print(f"  ✗ 测试失败: {e}")
        return False


def test_page_permissions():
    """测试页面权限配置"""
    print("\n测试 5: 页面权限配置...")
    try:
        from auth import PAGE_PERMISSIONS

        required_keys = ['public', 'user', 'admin']

        for key in required_keys:
            if key in PAGE_PERMISSIONS:
                print(f"  ✓ PAGE_PERMISSIONS['{key}'] 存在")
            else:
                print(f"  ✗ PAGE_PERMISSIONS['{key}'] 缺失")
                return False

        # 检查是否包含预期路径
        if '/login' in PAGE_PERMISSIONS['public']:
            print("  ✓ /login 在公开页面中")
        else:
            print("  ✗ /login 未在公开页面中")
            return False

        if '/home' in PAGE_PERMISSIONS['user']:
            print("  ✓ /home 在用户页面中")
        else:
            print("  ✗ /home 未在用户页面中")
            return False

        if '/admin' in PAGE_PERMISSIONS['admin']:
            print("  ✓ /admin 在管理员页面中")
        else:
            print("  ✗ /admin 未在管理员页面中")
            return False

        return True
    except Exception as e:
        print(f"  ✗ 测试失败: {e}")
        return False


def test_admin_check():
    """测试管理员检查逻辑"""
    print("\n测试 6: 管理员检查逻辑...")
    try:
        from auth import is_admin, ADMIN_USERNAMES, ADMIN_ROLES

        # 测试管理员用户名列表
        expected_usernames = ['admin', 'administrator', 'superuser', 'root']
        if set(ADMIN_USERNAMES) == set(expected_usernames):
            print(f"  ✓ 管理员用户名列表正确")
        else:
            print(f"  ✗ 管理员用户名列表不正确")
            print(f"    预期: {expected_usernames}")
            print(f"    实际: {ADMIN_USERNAMES}")
            return False

        # 测试管理员角色列表
        expected_roles = ['admin', 'administrator', 'superuser', 'root']
        if set(ADMIN_ROLES) == set(expected_roles):
            print(f"  ✓ 管理员角色列表正确")
        else:
            print(f"  ✗ 管理员角色列表不正确")
            print(f"    预期: {expected_roles}")
            print(f"    实际: {ADMIN_ROLES}")
            return False

        return True
    except Exception as e:
        print(f"  ✗ 测试失败: {e}")
        return False


def test_backward_compatibility():
    """测试向后兼容性"""
    print("\n测试 7: 向后兼容性...")
    try:
        from auth import __all__

        required_exports = [
            'hash_password', 'verify_password',
            'create_user', 'authenticate_user', 'get_current_user',
            'login_required', 'admin_required',
            'create_session', 'destroy_session'
        ]

        missing = []
        for export in required_exports:
            if export not in __all__:
                missing.append(export)

        if not missing:
            print("  ✓ 所有必需的导出都存在")
            return True
        else:
            print(f"  ✗ 缺失的导出: {', '.join(missing)}")
            return False

    except Exception as e:
        print(f"  ✗ 测试失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("="* 60)
    print("  统一认证模块测试")
    print("="* 60)

    tests = [
        test_imports,
        test_password_functions,
        test_role_constants,
        test_decorators_exist,
        test_page_permissions,
        test_admin_check,
        test_backward_compatibility
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
        print("\n✅ 所有测试通过! 认证模块可以安全使用")
        return 0
    else:
        print("\n❌ 部分测试失败,请检查问题")
        return 1


if __name__ == '__main__':
    exit(main())
