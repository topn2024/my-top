#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

# 测试管理员权限和控制台功能
BASE_URL = "http://localhost:3001"

def test_admin_login():
    """测试管理员登录"""
    session = requests.Session()

    # 测试登录接口
    login_data = {
        "username": "admin",
        "password": "TopN@2024"
    }

    print("正在测试管理员登录...")
    response = session.post(f"{BASE_URL}/api/auth/login", json=login_data)
    print(f"登录响应状态码: {response.status_code}")
    print(f"登录响应内容: {response.text}")

    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print("登录成功!")
            return session
        else:
            print(f"登录失败: {data.get('message', '未知错误')}")
    else:
        print("登录请求失败")

    return None

def test_admin_dashboard(session):
    """测试管理控制台访问"""
    print("\n正在测试管理控制台访问...")
    response = session.get(f"{BASE_URL}/admin")
    print(f"控制台响应状态码: {response.status_code}")

    if response.status_code == 200:
        print("管理控制台访问成功!")
        content = response.text

        # 检查是否包含模板管理相关内容
        if "模板管理" in content or "template" in content.lower():
            print("控制台包含模板管理功能")
        else:
            print("控制台未发现模板管理功能")

        # 检查数据分析功能
        if "数据分析" in content or "data analysis" in content.lower():
            print("控制台包含数据分析功能")
        else:
            print("控制台未发现数据分析功能")

        # 保存响应内容到文件供检查
        with open('admin_dashboard_test.html', 'w', encoding='utf-8') as f:
            f.write(content)
        print("控制台页面已保存到 admin_dashboard_test.html")

    else:
        print(f"管理控制台访问失败: {response.status_code}")
        print(f"响应内容: {response.text}")

def main():
    print("=== 测试管理员功能 ===")
    session = test_admin_login()

    if session:
        test_admin_dashboard(session)
    else:
        print("登录失败，无法测试管理控制台")

if __name__ == "__main__":
    main()