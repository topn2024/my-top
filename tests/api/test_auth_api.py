#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证API接口测试
测试用户登录、注册、权限验证等API端点
"""
import pytest
import requests
import json
from typing import Dict, Any
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.utils.api_client import APIClient
from tests.utils.test_helpers import get_test_config, generate_test_user_data


class TestAuthAPI:
    """认证API测试类"""

    @pytest.fixture(scope="class")
    def api_client(self):
        """API客户端fixture"""
        config = get_test_config()
        return APIClient(config['base_url'], config['timeout'])

    @pytest.fixture(scope="class")
    def test_user(self):
        """测试用户数据fixture"""
        return generate_test_user_data()

    def test_api_health_check(self, api_client):
        """测试API健康检查"""
        response = api_client.get("/")

        assert response.status_code == 200
        assert "TOP_N" in response.text
        print("✓ API健康检查通过")

    def test_login_page_access(self, api_client):
        """测试登录页面访问"""
        response = api_client.get("/login")

        assert response.status_code == 200
        assert "login" in response.text.lower() or "登录" in response.text
        print("✓ 登录页面访问正常")

    def test_user_registration_success(self, api_client, test_user):
        """测试用户注册成功"""
        # 首先确保用户不存在
        username = test_user['username']
        email = test_user['email']

        # 注册新用户
        register_data = {
            'username': username,
            'password': test_user['password'],
            'email': email,
            'confirm_password': test_user['password']
        }

        response = api_client.post("/api/register", data=register_data)

        # 注意：根据实际API实现调整断言
        assert response.status_code in [200, 201, 302]  # 302表示重定向到登录页

        if response.status_code == 302:
            # 重定向表示注册成功
            assert 'login' in response.headers.get('Location', '')

        print(f"✓ 用户注册测试通过: {username}")

    def test_user_login_success(self, api_client, test_user):
        """测试用户登录成功"""
        login_data = {
            'username': test_user['username'],
            'password': test_user['password']
        }

        response = api_client.post("/api/login", data=login_data)

        # 检查登录成功响应
        assert response.status_code in [200, 302]

        if response.status_code == 200:
            # JSON响应
            data = response.json() if response.headers.get('content-type') == 'application/json' else {}
            assert data.get('success') or data.get('token') or 'success' in response.text.lower()
        elif response.status_code == 302:
            # 重定向到主页
            assert 'dashboard' in response.headers.get('Location', '') or 'analysis' in response.headers.get('Location', '')

        print(f"✓ 用户登录测试通过: {test_user['username']}")

    def test_user_login_failure_wrong_password(self, api_client, test_user):
        """测试用户登录失败 - 错误密码"""
        login_data = {
            'username': test_user['username'],
            'password': 'wrong_password_123456'
        }

        response = api_client.post("/api/login", data=login_data)

        assert response.status_code in [401, 400, 200]  # 200但返回错误信息

        if response.status_code == 200:
            assert 'error' in response.text.lower() or '失败' in response.text or 'invalid' in response.text.lower()

        print("✓ 错误密码登录失败测试通过")

    def test_user_login_failure_nonexistent_user(self, api_client):
        """测试用户登录失败 - 用户不存在"""
        login_data = {
            'username': 'nonexistent_user_12345',
            'password': 'some_password_123'
        }

        response = api_client.post("/api/login", data=login_data)

        assert response.status_code in [401, 400, 200]

        if response.status_code == 200:
            assert 'error' in response.text.lower() or '失败' in response.text

        print("✓ 不存在用户登录失败测试通过")

    def test_protected_route_without_auth(self, api_client):
        """测试未授权访问受保护路由"""
        protected_routes = [
            '/api/user/profile',
            '/api/workflows',
            '/api/articles',
            '/api/publish'
        ]

        for route in protected_routes:
            response = api_client.get(route)
            assert response.status_code in [401, 403, 302]  # 302表示重定向到登录页

        print("✓ 未授权访问保护路由测试通过")

    def test_session_management(self, api_client, test_user):
        """测试会话管理"""
        # 先登录
        login_data = {
            'username': test_user['username'],
            'password': test_user['password']
        }

        login_response = api_client.post("/api/login", data=login_data)

        # 检查会话是否建立
        session_cookie = api_client.session.cookies.get('session')

        # 访问需要认证的页面
        profile_response = api_client.get("/api/user/profile")

        # 应该能够访问
        assert profile_response.status_code in [200, 302]

        print("✓ 会话管理测试通过")

    def test_logout_functionality(self, api_client, test_user):
        """测试登出功能"""
        # 先登录
        login_data = {
            'username': test_user['username'],
            'password': test_user['password']
        }

        api_client.post("/api/login", data=login_data)

        # 登出
        logout_response = api_client.post("/api/logout") or api_client.get("/logout")

        assert logout_response.status_code in [200, 302]

        # 检查登出后无法访问受保护路由
        profile_response = api_client.get("/api/user/profile")
        assert profile_response.status_code in [401, 403, 302]

        print("✓ 登出功能测试通过")

    def test_api_response_format(self, api_client):
        """测试API响应格式"""
        # 测试API响应头
        response = api_client.get("/api/health")

        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            assert 'application/json' in content_type or 'text/html' in content_type

        print("✓ API响应格式测试通过")

    def test_error_handling(self, api_client):
        """测试错误处理"""
        # 测试404错误
        response = api_client.get("/api/nonexistent/endpoint")
        assert response.status_code == 404

        # 测试无效方法
        response = api_client.delete("/api/login")
        assert response.status_code in [405, 404]

        print("✓ 错误处理测试通过")


if __name__ == "__main__":
    # 可以直接运行单个测试文件
    pytest.main([__file__, "-v", "-s"])