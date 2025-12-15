#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一日志配置模块
提供标准化的日志记录功能
"""
import logging
import sys
import os
from datetime import datetime
from functools import wraps
import traceback

# 日志目录
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# 日志格式
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def setup_logger(name=None, level=logging.INFO):
    """
    配置并返回logger实例

    Args:
        name: logger名称，默认为调用模块名
        level: 日志级别，默认INFO

    Returns:
        配置好的logger实例
    """
    logger = logging.getLogger(name or __name__)

    # 避免重复添加handler
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 文件处理器 - 所有日志
    all_log_file = os.path.join(LOG_DIR, 'all.log')
    file_handler = logging.FileHandler(all_log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # 文件处理器 - 错误日志
    error_log_file = os.path.join(LOG_DIR, 'error.log')
    error_handler = logging.FileHandler(error_log_file, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    logger.addHandler(error_handler)

    return logger


def log_function_call(logger=None):
    """
    装饰器：记录函数调用的详细信息

    用法:
        @log_function_call()
        def my_function(arg1, arg2):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_logger = logger or logging.getLogger(func.__module__)
            func_name = func.__name__

            # 记录函数调用开始
            func_logger.info(f">>> Calling {func_name}")
            func_logger.debug(f"    Args: {args}")
            func_logger.debug(f"    Kwargs: {kwargs}")

            start_time = datetime.now()

            try:
                result = func(*args, **kwargs)

                # 记录函数调用成功
                elapsed = (datetime.now() - start_time).total_seconds()
                func_logger.info(f"<<< {func_name} completed successfully in {elapsed:.3f}s")

                return result

            except Exception as e:
                # 记录函数调用失败
                elapsed = (datetime.now() - start_time).total_seconds()
                func_logger.error(f"!!! {func_name} failed after {elapsed:.3f}s")
                func_logger.error(f"    Error: {str(e)}")
                func_logger.error(f"    Traceback: {traceback.format_exc()}")
                raise

        return wrapper
    return decorator


def log_api_request(operation_description=None):
    """
    装饰器：记录API请求的详细信息（业务语义化）

    用法:
        @app.route('/api/example')
        @log_api_request("创建用户订单")
        def example_api():
            ...

    Args:
        operation_description: 操作描述，如"创建提示词模板"、"更新用户信息"
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from flask import request, session as flask_session
            import json

            func_logger = logging.getLogger(func.__module__)

            # 生成请求ID用于追踪
            import uuid
            request_id = str(uuid.uuid4())[:8]

            # 获取用户信息
            user_id = flask_session.get('user_id', 'anonymous')

            # 提取关键业务参数
            business_params = {}
            if request.is_json:
                body = request.get_json() or {}
                # 记录关键业务字段，隐藏敏感信息
                for key, value in body.items():
                    if 'password' in key.lower() or 'token' in key.lower() or 'secret' in key.lower():
                        business_params[key] = '***HIDDEN***'
                    elif isinstance(value, (str, int, float, bool)):
                        business_params[key] = value
                    elif isinstance(value, dict):
                        business_params[key] = f"<dict with {len(value)} keys>"
                    elif isinstance(value, list):
                        business_params[key] = f"<list with {len(value)} items>"

            # 获取路径参数
            path_params = {}
            if kwargs:
                for key, value in kwargs.items():
                    if not key.startswith('_'):
                        path_params[key] = value

            # 获取查询参数
            query_params = dict(request.args)

            # 构建操作描述
            operation = operation_description or f"{request.method} {func.__name__}"

            # ====== 请求开始日志 ======
            func_logger.info(f"╔{'═'*80}╗")
            func_logger.info(f"║ 【请求开始】{operation}")
            func_logger.info(f"║ RequestID: {request_id} | User: {user_id}")
            func_logger.info(f"║ Endpoint: {request.method} {request.path}")

            if path_params:
                func_logger.info(f"║ 路径参数: {json.dumps(path_params, ensure_ascii=False)}")
            if query_params:
                func_logger.info(f"║ 查询参数: {json.dumps(query_params, ensure_ascii=False)}")
            if business_params:
                func_logger.info(f"║ 请求数据: {json.dumps(business_params, ensure_ascii=False, indent=2)}")

            start_time = datetime.now()

            try:
                # 执行业务逻辑
                func_logger.info(f"║ 开始执行业务逻辑...")
                response = func(*args, **kwargs)

                # 解析响应
                elapsed = (datetime.now() - start_time).total_seconds()
                status = getattr(response, 'status_code', 200) if hasattr(response, 'status_code') else 200

                # 提取响应关键信息
                response_info = ""
                business_success = True  # 业务是否成功
                json_parse_failed = False
                if hasattr(response, 'get_json'):
                    try:
                        resp_data = response.get_json()
                        if isinstance(resp_data, dict):
                            if 'success' in resp_data:
                                business_success = resp_data.get('success', True)
                                response_info = f"success={business_success}"
                            if 'data' in resp_data and isinstance(resp_data['data'], dict):
                                response_info += f", data_keys={list(resp_data['data'].keys())}"
                            if 'error' in resp_data:
                                response_info += f", error={resp_data.get('error')}"
                    except Exception as json_err:
                        # JSON解析失败（可能返回的是HTML错误页面）
                        json_parse_failed = True
                        business_success = False
                        response_info = f"响应格式错误（非JSON）: {str(json_err)[:100]}"

                # ====== 请求完成日志 ======
                func_logger.info(f"║ 执行完成: 耗时 {elapsed:.3f}s | 状态码 {status}")
                if response_info:
                    func_logger.info(f"║ 响应信息: {response_info}")
                func_logger.info(f"╚{'═'*80}╝")

                # 根据业务成功状态显示不同的日志
                if status >= 400 or not business_success:
                    func_logger.warning(f"⚠ [{operation}] 执行失败 (RequestID: {request_id})")
                else:
                    func_logger.info(f"✓ [{operation}] 成功完成 (RequestID: {request_id})")

                return response

            except Exception as e:
                # ====== 请求失败日志 ======
                elapsed = (datetime.now() - start_time).total_seconds()
                func_logger.error(f"║ 执行失败: 耗时 {elapsed:.3f}s")
                func_logger.error(f"╚{'═'*80}╝")
                func_logger.error(f"✗ [{operation}] 执行失败 (RequestID: {request_id})")
                func_logger.error(f"错误类型: {type(e).__name__}")
                func_logger.error(f"错误信息: {str(e)}")
                func_logger.error(f"错误堆栈:\n{traceback.format_exc()}")
                raise

        return wrapper
    return decorator


def log_service_call(operation_name):
    """
    装饰器：记录服务层操作

    用法:
        @log_service_call("分析公司信息")
        def analyze_company(company_name):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_logger = logging.getLogger(func.__module__)

            # 记录操作开始
            func_logger.info(f"[Service] {operation_name} - 开始")
            func_logger.debug(f"    Function: {func.__name__}")
            func_logger.debug(f"    Args: {args}")
            func_logger.debug(f"    Kwargs: {kwargs}")

            start_time = datetime.now()

            try:
                result = func(*args, **kwargs)

                # 记录操作成功
                elapsed = (datetime.now() - start_time).total_seconds()
                func_logger.info(f"[Service] {operation_name} - 完成 ({elapsed:.3f}s)")

                return result

            except Exception as e:
                # 记录操作失败
                elapsed = (datetime.now() - start_time).total_seconds()
                func_logger.error(f"[Service] {operation_name} - 失败 ({elapsed:.3f}s)")
                func_logger.error(f"    Error: {str(e)}")
                func_logger.error(f"    Traceback: {traceback.format_exc()}")
                raise

        return wrapper
    return decorator


# 默认logger
default_logger = setup_logger('topn_platform')
