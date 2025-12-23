#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
from urllib.parse import urlparse

def test_admin_like_browser():
    """模拟浏览器行为测试管理控制台"""
    session = requests.Session()

    # 第一步：登录
    print("=== 第一步：登录 ===")
    login_data = {
        "username": "admin",
        "password": "TopN@2024"
    }

    login_response = session.post("http://localhost:3001/api/auth/login", json=login_data)
    print(f"登录状态码: {login_response.status_code}")

    if login_response.status_code == 200:
        login_result = login_response.json()
        if login_result.get('success'):
            print("✓ 登录成功")
            print(f"用户信息: {login_result.get('user', {})}")

            # 第二步：访问管理控制台
            print("\n=== 第二步：访问管理控制台 ===")
            admin_response = session.get("http://localhost:3001/admin")
            print(f"管理控制台状态码: {admin_response.status_code}")

            if admin_response.status_code == 200:
                print("✓ 管理控制台访问成功")

                # 检查响应内容
                content = admin_response.text
                if "管理控制台" in content:
                    print("✓ 页面内容正确")
                else:
                    print("✗ 页面内容异常")

                # 第三步：测试用户信息API
                print("\n=== 第三步：测试用户信息API ===")
                me_response = session.get("http://localhost:3001/api/auth/me")
                print(f"用户信息API状态码: {me_response.status_code}")

                if me_response.status_code == 200:
                    me_data = me_response.json()
                    print(f"用户信息: {me_data}")

                    if me_data.get('success') and me_data.get('user', {}).get('role') == 'admin':
                        print("✓ 用户权限验证成功")
                    else:
                        print("✗ 用户权限验证失败")
                else:
                    print("✗ 用户信息API访问失败")

            else:
                print("✗ 管理控制台访问失败")
                print(f"错误内容: {admin_response.text[:500]}")
        else:
            print(f"✗ 登录失败: {login_result.get('message', '未知错误')}")
    else:
        print(f"✗ 登录请求失败: {login_response.status_code}")

if __name__ == "__main__":
    print("=== 模拟浏览器访问管理控制台 ===")
    test_admin_like_browser()