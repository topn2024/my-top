#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 blueprints 架构的应用（服务器版本）
"""

import sys
import os

# 添加 backend 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app_factory import create_app

# 创建应用实例（生产配置）
app = create_app('production')

def test_server_app():
    """测试服务器架构的应用"""
    print("=" * 60)
    print("测试 Blueprints 架构应用（服务器版本）")
    print("=" * 60)
    print()

    with app.test_client() as client:
        # 测试1：登录
        print("测试 1: 用户登录")
        login_response = client.post(
            '/api/auth/login',
            json={
                'username': 'admin',
                'password': 'TopN@2024'
            },
            content_type='application/json'
        )
        print(f"  状态码: {login_response.status_code}")

        if login_response.status_code == 200:
            login_data = login_response.json
            print(f"  登录成功: {login_data.get('success')}")
            print(f"  用户信息: {login_data.get('user', {})}")
        else:
            print(f"  登录失败: {login_response.data.decode()}")
            return

        print()

        # 测试2：获取当前用户信息
        print("测试 2: 获取当前用户信息")
        me_response = client.get('/api/auth/me')
        print(f"  状态码: {me_response.status_code}")

        if me_response.status_code == 200:
            me_data = me_response.json
            print(f"  成功: {me_data.get('success')}")
            user = me_data.get('user', {})
            print(f"  用户名: {user.get('username')}")
            print(f"  角色: {user.get('role')}")
        else:
            print(f"  失败: {me_response.data.decode()}")

        print()

        # 测试3：访问管理控制台
        print("测试 3: 访问管理控制台")
        admin_response = client.get('/admin')
        print(f"  状态码: {admin_response.status_code}")

        if admin_response.status_code == 200:
            print("  [OK] 管理控制台访问成功")
            # 检查返回内容
            content = admin_response.data.decode('utf-8')
            if '管理控制台' in content:
                print("  [OK] 页面内容正确")
            else:
                print("  [FAIL] 页面内容异常")
        else:
            print(f"  [FAIL] 管理控制台访问失败")
            error_data = admin_response.data.decode('utf-8')
            print(f"  错误: {error_data[:200]}")

        print()

        # 测试4：访问模板管理页面
        print("测试 4: 访问模板管理页面")
        templates_response = client.get('/templates')
        print(f"  状态码: {templates_response.status_code}")

        if templates_response.status_code == 200:
            print("  [OK] 模板管理页面访问成功")
        else:
            print(f"  [FAIL] 模板管理页面访问失败")

        print()

    print("=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == '__main__':
    test_server_app()
