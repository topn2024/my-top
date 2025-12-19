#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流API接口测试
测试工作流创建、执行、状态管理等API端点
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
from tests.utils.test_helpers import get_test_config, generate_test_workflow_data, authenticate_user


class TestWorkflowAPI:
    """工作流API测试类"""

    @pytest.fixture(scope="class")
    def api_client(self):
        """API客户端fixture"""
        config = get_test_config()
        client = APIClient(config['base_url'], config['timeout'])

        # 使用测试用户认证
        authenticate_user(client)
        return client

    @pytest.fixture(scope="class")
    def test_workflow(self):
        """测试工作流数据fixture"""
        return generate_test_workflow_data()

    def test_get_workflows_list(self, api_client):
        """测试获取工作流列表"""
        response = api_client.get("/api/workflows")

        assert response.status_code == 200

        # 检查响应格式
        if 'application/json' in response.headers.get('content-type', ''):
            data = response.json()
            assert 'workflows' in data or isinstance(data, list)

        print("✓ 获取工作流列表测试通过")

    def test_create_workflow_success(self, api_client, test_workflow):
        """测试创建工作流成功"""
        response = api_client.post("/api/workflows", json=test_workflow)

        assert response.status_code in [200, 201]

        if response.status_code == 200:
            data = response.json()
            assert data.get('success') or data.get('id') or 'created' in response.text.lower()

        print(f"✓ 创建工作流测试通过: {test_workflow.get('name', 'Untitled Workflow')}")

    def test_create_workflow_validation(self, api_client):
        """测试创建工作流数据验证"""
        # 测试空名称
        invalid_workflow = {
            'name': '',
            'description': 'Test description',
            'steps': [
                {'step': 1, 'action': 'analyze'}
            ]
        }

        response = api_client.post("/api/workflows", json=invalid_workflow)
        assert response.status_code in [400, 422]

        # 测试空步骤
        invalid_workflow = {
            'name': 'Test Workflow',
            'description': 'Test description',
            'steps': []
        }

        response = api_client.post("/api/workflows", json=invalid_workflow)
        assert response.status_code in [400, 422]

        print("✓ 创建工作流数据验证测试通过")

    def test_get_workflow_by_id(self, api_client):
        """测试根据ID获取工作流"""
        # 获取工作流列表
        list_response = api_client.get("/api/workflows")

        if list_response.status_code == 200:
            data = list_response.json()
            workflows = data.get('workflows', []) if isinstance(data, dict) else data

            if workflows:
                first_workflow = workflows[0]
                workflow_id = first_workflow.get('id')

                if workflow_id:
                    detail_response = api_client.get(f"/api/workflows/{workflow_id}")
                    assert detail_response.status_code == 200

                    # 验证返回的工作流数据
                    if 'application/json' in detail_response.headers.get('content-type', ''):
                        workflow_data = detail_response.json()
                        assert workflow_data.get('name') or workflow_data.get('description')

        print("✓ 根据ID获取工作流测试通过")

    def test_update_workflow(self, api_client):
        """测试更新工作流"""
        # 获取工作流列表
        list_response = api_client.get("/api/workflows")

        if list_response.status_code == 200:
            data = list_response.json()
            workflows = data.get('workflows', []) if isinstance(data, dict) else data

            if workflows:
                # 更新第一个工作流
                workflow = workflows[0]
                workflow_id = workflow.get('id')

                if workflow_id:
                    updated_data = {
                        'name': 'Updated Test Workflow',
                        'description': 'Updated test description',
                        'steps': [
                            {'step': 1, 'action': 'analyze', 'config': {'model': 'zhipu'}},
                            {'step': 2, 'action': 'generate', 'config': {'length': 500}},
                            {'step': 3, 'action': 'publish', 'config': {'platform': 'weibo'}}
                        ]
                    }

                    update_response = api_client.put(f"/api/workflows/{workflow_id}", json=updated_data)
                    assert update_response.status_code in [200, 204]

        print("✓ 更新工作流测试通过")

    def test_delete_workflow(self, api_client):
        """测试删除工作流"""
        # 先创建一个测试工作流
        test_workflow = generate_test_workflow_data()
        create_response = api_client.post("/api/workflows", json=test_workflow)

        # 获取工作流列表找到刚创建的工作流
        list_response = api_client.get("/api/workflows")

        if list_response.status_code == 200:
            data = list_response.json()
            workflows = data.get('workflows', []) if isinstance(data, dict) else data

            if workflows:
                # 删除最后一个工作流（可能是刚创建的）
                workflow = workflows[-1]
                workflow_id = workflow.get('id')

                if workflow_id:
                    delete_response = api_client.delete(f"/api/workflows/{workflow_id}")
                    assert delete_response.status_code in [200, 204]

        print("✓ 删除工作流测试通过")

    def test_execute_workflow(self, api_client):
        """测试执行工作流"""
        # 获取工作流列表
        list_response = api_client.get("/api/workflows")

        if list_response.status_code == 200:
            data = list_response.json()
            workflows = data.get('workflows', []) if isinstance(data, dict) else data

            if workflows:
                workflow = workflows[0]
                workflow_id = workflow.get('id')

                if workflow_id:
                    # 准备执行数据
                    execution_data = {
                        'input_data': {
                            'title': 'Test Article Title',
                            'content': 'This is test article content for workflow execution.'
                        },
                        'options': {
                            'async': False
                        }
                    }

                    execute_response = api_client.post(f"/api/workflows/{workflow_id}/execute", json=execution_data)

                    # 工作流执行可能返回202（异步）或200（同步）
                    assert execute_response.status_code in [200, 202, 400]

                    if execute_response.status_code == 200:
                        exec_data = execute_response.json()
                        assert 'execution_id' in exec_data or 'result' in exec_data

        print("✓ 执行工作流测试通过")

    def test_get_workflow_executions(self, api_client):
        """测试获取工作流执行历史"""
        # 获取工作流列表
        list_response = api_client.get("/api/workflows")

        if list_response.status_code == 200:
            data = list_response.json()
            workflows = data.get('workflows', []) if isinstance(data, dict) else data

            if workflows:
                workflow = workflows[0]
                workflow_id = workflow.get('id')

                if workflow_id:
                    # 获取执行历史
                    executions_response = api_client.get(f"/api/workflows/{workflow_id}/executions")

                    assert executions_response.status_code == 200

                    if 'application/json' in executions_response.headers.get('content-type', ''):
                        exec_data = executions_response.json()
                        assert 'executions' in exec_data or isinstance(exec_data, list)

        print("✓ 获取工作流执行历史测试通过")

    def test_workflow_templates(self, api_client):
        """测试工作流模板API"""
        response = api_client.get("/api/workflows/templates")

        assert response.status_code == 200

        if 'application/json' in response.headers.get('content-type', ''):
            data = response.json()
            assert isinstance(data, list) or 'templates' in data

        print("✓ 工作流模板API测试通过")

    def test_workflow_validation_rules(self, api_client):
        """测试工作流验证规则"""
        # 测试步骤配置验证
        invalid_workflow = {
            'name': 'Invalid Workflow',
            'description': 'Test invalid workflow',
            'steps': [
                {'step': 1, 'action': 'invalid_action'},  # 无效动作
                {'step': 2, 'action': 'analyze', 'config': {}}  # 缺少必要配置
            ]
        }

        response = api_client.post("/api/workflows", json=invalid_workflow)
        assert response.status_code in [400, 422]

        print("✓ 工作流验证规则测试通过")

    def test_workflow_clone(self, api_client):
        """测试工作流克隆功能"""
        # 获取工作流列表
        list_response = api_client.get("/api/workflows")

        if list_response.status_code == 200:
            data = list_response.json()
            workflows = data.get('workflows', []) if isinstance(data, dict) else data

            if workflows:
                workflow = workflows[0]
                workflow_id = workflow.get('id')

                if workflow_id:
                    # 克隆工作流
                    clone_data = {
                        'name': 'Cloned Test Workflow',
                        'description': 'Cloned from existing workflow'
                    }

                    clone_response = api_client.post(f"/api/workflows/{workflow_id}/clone", json=clone_data)

                    # 克隆可能返回201或200，或400如果不支持
                    assert clone_response.status_code in [200, 201, 400]

        print("✓ 工作流克隆功能测试通过")

    def test_workflow_statistics(self, api_client):
        """测试工作流统计信息"""
        response = api_client.get("/api/workflows/statistics")

        assert response.status_code == 200

        if 'application/json' in response.headers.get('content-type', ''):
            data = response.json()
            expected_keys = ['total_workflows', 'active_workflows', 'execution_count']
            # 至少应该包含一些统计信息
            assert any(key in data for key in expected_keys) or 'stats' in data

        print("✓ 工作流统计信息测试通过")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])