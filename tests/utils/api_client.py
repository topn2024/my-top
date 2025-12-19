#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API客户端工具
提供统一的HTTP请求接口和会话管理
"""
import requests
import json
from typing import Dict, Any, Optional, Union
from urllib.parse import urljoin


class APIClient:
    """API客户端类"""

    def __init__(self, base_url: str, timeout: int = 30):
        """
        初始化API客户端

        Args:
            base_url: 基础URL
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()

        # 设置默认请求头
        self.session.headers.update({
            'User-Agent': 'TOP-N-Test-Client/1.0',
            'Accept': 'application/json, text/html',
            'Content-Type': 'application/json'
        })

    def _make_request(self, method: str, endpoint: str,
                     data: Optional[Dict] = None,
                     json_data: Optional[Dict] = None,
                     params: Optional[Dict] = None,
                     files: Optional[Dict] = None,
                     **kwargs) -> requests.Response:
        """
        发送HTTP请求

        Args:
            method: HTTP方法
            endpoint: API端点
            data: 表单数据
            json_data: JSON数据
            params: URL参数
            files: 上传文件
            **kwargs: 其他requests参数

        Returns:
            requests.Response对象
        """
        url = urljoin(f"{self.base_url}/", endpoint.lstrip('/'))

        # 准备请求参数
        request_kwargs = {
            'timeout': self.timeout,
            'params': params,
            **kwargs
        }

        if data:
            request_kwargs['data'] = data
            # 如果有表单数据，移除JSON内容类型
            if 'Content-Type' in self.session.headers:
                del self.session.headers['Content-Type']

        if json_data:
            request_kwargs['json'] = json_data

        if files:
            request_kwargs['files'] = files
            # 如果有文件上传，移除JSON内容类型
            if 'Content-Type' in self.session.headers:
                del self.session.headers['Content-Type']

        try:
            response = self.session.request(method, url, **request_kwargs)
            return response
        except requests.exceptions.RequestException as e:
            raise Exception(f"请求失败: {method} {url} - {str(e)}")

    def get(self, endpoint: str, params: Optional[Dict] = None, **kwargs) -> requests.Response:
        """GET请求"""
        return self._make_request('GET', endpoint, params=params, **kwargs)

    def post(self, endpoint: str, data: Optional[Dict] = None,
             json_data: Optional[Dict] = None, **kwargs) -> requests.Response:
        """POST请求"""
        return self._make_request('POST', endpoint, data=data, json_data=json_data, **kwargs)

    def put(self, endpoint: str, data: Optional[Dict] = None,
            json_data: Optional[Dict] = None, **kwargs) -> requests.Response:
        """PUT请求"""
        return self._make_request('PUT', endpoint, data=data, json_data=json_data, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """DELETE请求"""
        return self._make_request('DELETE', endpoint, **kwargs)

    def patch(self, endpoint: str, data: Optional[Dict] = None,
              json_data: Optional[Dict] = None, **kwargs) -> requests.Response:
        """PATCH请求"""
        return self._make_request('PATCH', endpoint, data=data, json_data=json_data, **kwargs)

    def set_auth_token(self, token: str):
        """设置认证token"""
        self.session.headers['Authorization'] = f'Bearer {token}'

    def set_cookie(self, name: str, value: str):
        """设置cookie"""
        self.session.cookies.set(name, value)

    def get_cookie(self, name: str) -> Optional[str]:
        """获取cookie值"""
        return self.session.cookies.get(name)

    def clear_cookies(self):
        """清除所有cookies"""
        self.session.cookies.clear()

    def close(self):
        """关闭会话"""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class APITestClient(APIClient):
    """专门用于测试的API客户端"""

    def __init__(self, base_url: str, timeout: int = 30, test_mode: bool = True):
        super().__init__(base_url, timeout)
        self.test_mode = test_mode

        if test_mode:
            # 设置测试模式请求头
            self.session.headers.update({
                'X-Test-Mode': 'true',
                'X-Test-Client': 'python-requests'
            })

    def assert_response_success(self, response: requests.Response,
                             expected_status: int = 200,
                             allow_redirect: bool = True):
        """
        断言响应成功

        Args:
            response: 响应对象
            expected_status: 期望的状态码
            allow_redirect: 是否允许重定向
        """
        if allow_redirect and response.status_code in [301, 302, 303, 307, 308]:
            # 重定向在某些情况下是成功的
            return

        assert response.status_code == expected_status, \
            f"期望状态码 {expected_status}，实际 {response.status_code}，响应内容: {response.text[:200]}"

    def assert_json_response(self, response: requests.Response):
        """
        断言JSON响应

        Args:
            response: 响应对象
        """
        content_type = response.headers.get('content-type', '').lower()
        assert 'application/json' in content_type, \
            f"期望JSON响应，实际Content-Type: {content_type}"

    def get_json_data(self, response: requests.Response) -> Dict[str, Any]:
        """
        获取JSON响应数据

        Args:
            response: 响应对象

        Returns:
            JSON数据字典
        """
        self.assert_json_response(response)
        try:
            return response.json()
        except json.JSONDecodeError as e:
            raise ValueError(f"解析JSON响应失败: {str(e)}, 响应内容: {response.text}")

    def assert_field_exists(self, response: requests.Response, field_name: str):
        """
        断言响应中包含指定字段

        Args:
            response: 响应对象
            field_name: 字段名
        """
        data = self.get_json_data(response)
        assert field_name in data, f"响应中缺少字段: {field_name}"

    def assert_field_equals(self, response: requests.Response,
                          field_name: str, expected_value: Any):
        """
        断言响应字段等于期望值

        Args:
            response: 响应对象
            field_name: 字段名
            expected_value: 期望值
        """
        data = self.get_json_data(response)
        actual_value = data.get(field_name)
        assert actual_value == expected_value, \
            f"字段 {field_name} 期望值 {expected_value}，实际值 {actual_value}"

    def wait_for_async_result(self, check_endpoint: str,
                            max_wait: int = 30,
                            check_interval: int = 2) -> Dict[str, Any]:
        """
        等待异步操作结果

        Args:
            check_endpoint: 检查结果的端点
            max_wait: 最大等待时间（秒）
            check_interval: 检查间隔（秒）

        Returns:
            最终的结果数据
        """
        import time

        start_time = time.time()

        while time.time() - start_time < max_wait:
            response = self.get(check_endpoint)

            if response.status_code == 200:
                data = self.get_json_data(response)

                # 检查是否完成
                if data.get('status') == 'completed':
                    return data
                elif data.get('status') == 'failed':
                    raise Exception(f"异步操作失败: {data.get('error', '未知错误')}")

            time.sleep(check_interval)

        raise TimeoutError(f"等待异步结果超时: {max_wait}秒")