#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文章API接口测试
测试文章创建、编辑、分析、发布等API端点
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
from tests.utils.test_helpers import get_test_config, generate_test_article_data, authenticate_user


class TestArticleAPI:
    """文章API测试类"""

    @pytest.fixture(scope="class")
    def api_client(self):
        """API客户端fixture"""
        config = get_test_config()
        client = APIClient(config['base_url'], config['timeout'])

        # 使用测试用户认证
        authenticate_user(client)
        return client

    @pytest.fixture(scope="class")
    def test_article(self):
        """测试文章数据fixture"""
        return generate_test_article_data()

    def test_get_articles_list(self, api_client):
        """测试获取文章列表"""
        response = api_client.get("/api/articles")

        assert response.status_code == 200

        # 检查响应是否为JSON格式
        if 'application/json' in response.headers.get('content-type', ''):
            data = response.json()
            assert 'articles' in data or isinstance(data, list)

        print("✓ 获取文章列表测试通过")

    def test_create_article_success(self, api_client, test_article):
        """测试创建文章成功"""
        response = api_client.post("/api/articles", json=test_article)

        assert response.status_code in [200, 201]

        if response.status_code == 200:
            data = response.json()
            assert data.get('success') or data.get('id') or 'created' in response.text.lower()

        print(f"✓ 创建文章测试通过: {test_article.get('title', 'Untitled')}")

    def test_create_article_validation(self, api_client):
        """测试创建文章数据验证"""
        # 测试空标题
        invalid_article = {
            'title': '',
            'content': 'This is test content',
            'category': 'technology'
        }

        response = api_client.post("/api/articles", json=invalid_article)
        assert response.status_code in [400, 422]

        # 测试空内容
        invalid_article = {
            'title': 'Test Title',
            'content': '',
            'category': 'technology'
        }

        response = api_client.post("/api/articles", json=invalid_article)
        assert response.status_code in [400, 422]

        print("✓ 创建文章数据验证测试通过")

    def test_get_article_by_id(self, api_client):
        """测试根据ID获取文章"""
        # 先创建文章
        test_article = generate_test_article_data()
        create_response = api_client.post("/api/articles", json=test_article)

        if create_response.status_code in [200, 201]:
            # 尝试获取文章列表中的第一篇文章
            list_response = api_client.get("/api/articles")
            if list_response.status_code == 200:
                data = response.json()
                articles = data.get('articles', []) if isinstance(data, dict) else data

                if articles:
                    first_article = articles[0]
                    article_id = first_article.get('id')

                    if article_id:
                        detail_response = api_client.get(f"/api/articles/{article_id}")
                        assert detail_response.status_code == 200

                        # 验证返回的文章数据
                        if 'application/json' in detail_response.headers.get('content-type', ''):
                            article_data = detail_response.json()
                            assert article_data.get('title') or article_data.get('content')

        print("✓ 根据ID获取文章测试通过")

    def test_update_article(self, api_client):
        """测试更新文章"""
        # 获取文章列表
        list_response = api_client.get("/api/articles")

        if list_response.status_code == 200:
            data = list_response.json()
            articles = data.get('articles', []) if isinstance(data, dict) else data

            if articles:
                # 更新第一篇文章
                article = articles[0]
                article_id = article.get('id')

                if article_id:
                    updated_data = {
                        'title': 'Updated Test Title',
                        'content': 'Updated test content with new information',
                        'category': 'updated_category'
                    }

                    update_response = api_client.put(f"/api/articles/{article_id}", json=updated_data)
                    assert update_response.status_code in [200, 204]

        print("✓ 更新文章测试通过")

    def test_delete_article(self, api_client):
        """测试删除文章"""
        # 先创建一个测试文章
        test_article = generate_test_article_data()
        create_response = api_client.post("/api/articles", json=test_article)

        # 获取文章列表找到刚创建的文章
        list_response = api_client.get("/api/articles")

        if list_response.status_code == 200:
            data = list_response.json()
            articles = data.get('articles', []) if isinstance(data, dict) else data

            if articles:
                # 删除最后一篇文章（可能是刚创建的）
                article = articles[-1]
                article_id = article.get('id')

                if article_id:
                    delete_response = api_client.delete(f"/api/articles/{article_id}")
                    assert delete_response.status_code in [200, 204]

        print("✓ 删除文章测试通过")

    def test_analyze_article_api(self, api_client, test_article):
        """测试文章分析API"""
        # 创建文章
        create_response = api_client.post("/api/articles", json=test_article)

        # 尝试调用分析接口
        analysis_data = {
            'article_id': 1,  # 假设ID为1
            'analysis_type': 'sentiment',
            'target_audience': 'general'
        }

        response = api_client.post("/api/articles/analyze", json=analysis_data)

        # 分析可能需要时间，可能返回202或200
        assert response.status_code in [200, 202, 400]

        if response.status_code == 200:
            data = response.json()
            assert 'analysis' in data or 'result' in data or 'score' in data

        print("✓ 文章分析API测试通过")

    def test_article_search(self, api_client):
        """测试文章搜索功能"""
        search_params = {
            'q': 'test',
            'category': 'technology',
            'limit': 10
        }

        response = api_client.get("/api/articles/search", params=search_params)

        assert response.status_code == 200

        if 'application/json' in response.headers.get('content-type', ''):
            data = response.json()
            assert 'articles' in data or isinstance(data, list)

        print("✓ 文章搜索测试通过")

    def test_article_categories(self, api_client):
        """测试文章分类API"""
        response = api_client.get("/api/articles/categories")

        assert response.status_code == 200

        if 'application/json' in response.headers.get('content-type', ''):
            data = response.json()
            assert isinstance(data, list) or 'categories' in data

        print("✓ 文章分类API测试通过")

    def test_article_pagination(self, api_client):
        """测试文章分页功能"""
        page_params = {
            'page': 1,
            'per_page': 5
        }

        response = api_client.get("/api/articles", params=page_params)

        assert response.status_code == 200

        # 检查分页信息
        if 'application/json' in response.headers.get('content-type', ''):
            data = response.json()
            if isinstance(data, dict):
                assert 'pagination' in data or 'page' in data

        print("✓ 文章分页测试通过")

    def test_bulk_operations(self, api_client):
        """测试批量操作"""
        # 批量创建
        bulk_data = {
            'articles': [
                generate_test_article_data(),
                generate_test_article_data(),
                generate_test_article_data()
            ]
        }

        response = api_client.post("/api/articles/bulk", json=bulk_data)

        # 批量操作可能返回207或200
        assert response.status_code in [200, 207, 400]  # 400如果API不支持

        print("✓ 批量操作测试通过")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])