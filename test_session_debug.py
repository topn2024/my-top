#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_session_debug():
    """测试 session 状态和权限检查"""
    session = requests.Session()

    # 第一步：登录
    print("=== 登录 ===")
    login_data = {
        "username": "admin",
        "password": "TopN@2024"
    }

    login_response = session.post("http://localhost:3001/api/auth/login", json=login_data)
    print(f"登录响应: {login_response.status_code}")

    if login_response.status_code == 200:
        login_result = login_response.json()
        print(f"登录成功: {login_result.get('success')}")

        # 第二步：测试管理控制台
        print("\n=== 测试管理控制台 ===")
        admin_response = session.get("http://localhost:3001/admin")
        print(f"管理控制台响应: {admin_response.status_code}")

        if admin_response.status_code == 401:
            print("权限不足 - session 未正确传递")
            print(f"响应内容: {admin_response.text}")
        elif admin_response.status_code == 200:
            print("管理控制台访问成功")
        else:
            print(f"其他错误: {admin_response.status_code}")
            print(f"响应内容: {admin_response.text[:500]}")

        # 第三步：检查API用户信息
        print("\n=== 检查用户信息API ===")
        me_response = session.get("http://localhost:3001/api/auth/me")
        print(f"用户信息API: {me_response.status_code}")

        if me_response.status_code == 200:
            me_data = me_response.json()
            print(f"当前用户: {me_data}")
        else:
            print(f"用户信息获取失败: {me_response.text}")

if __name__ == "__main__":
    test_session_debug()