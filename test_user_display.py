#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

# 测试用户显示功能
BASE_URL = "http://localhost:3001"

def test_current_user():
    """测试获取当前用户信息"""
    session = requests.Session()

    # 先登录
    login_data = {
        "username": "admin",
        "password": "TopN@2024"
    }

    print("正在登录管理员账号...")
    response = session.post(f"{BASE_URL}/api/auth/login", json=login_data)

    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print("登录成功!")

            # 测试获取当前用户信息
            print("\n正在获取当前用户信息...")
            response = session.get(f"{BASE_URL}/api/auth/me")

            if response.status_code == 200:
                user_data = response.json()
                print(f"当前用户信息: {json.dumps(user_data, indent=2, ensure_ascii=False)}")

                if user_data.get('user'):
                    user = user_data['user']
                    if user.get('role') == 'admin':
                        print("当前用户是管理员，应该能看到模板管理入口")
                    else:
                        print("当前用户不是管理员")
            else:
                print(f"获取用户信息失败: {response.status_code}")
        else:
            print(f"登录失败: {data.get('message', '未知错误')}")
    else:
        print("登录请求失败")

if __name__ == "__main__":
    print("=== 测试用户显示功能 ===")
    test_current_user()