#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版日志配置模块
提供完善的日志记录功能，方便问题定位和性能监控
"""
import logging
import sys
import os
import json
from datetime import datetime
from functools import wraps
import traceback
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from threading import local
import uuid

# 线程本地存储，用于存储请求ID
_thread_local = local()

# 日志目录
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# 日志格式
DETAILED_FORMAT = '%(asctime)s | %(levelname)-8s | %(name)-30s | [%(filename)s:%(lineno)4d] | %(request_id)s | %(message)s'
SIMPLE_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
JSON_FORMAT = True  # 是否启用JSON格式日志
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# 慢查询阈值（秒）
SLOW_QUERY_THRESHOLD = 3.0
SLOW_API_THRESHOLD = 2.0


class RequestIdFilter(logging.Filter):
    """为日志添加请求ID"""

    def filter(self, record):
        record.request_id = getattr(_thread_local, 'request_id', 'NO-REQ-ID')
        return True


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器（JSON格式）"""

    def format(self, record):
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'file': record.filename,
            'line': record.lineno,
            'function': record.funcName,
            'request_id': getattr(record, 'request_id', 'NO-REQ-ID'),
            'message': record.getMessage(),
        }

        # 添加异常信息
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # 添加额外字段
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'duration'):
            log_data['duration'] = record.duration
        if hasattr(record, 'operation'):
            log_data['operation'] = record.operation

        return json.dumps(log_data, ensure_ascii=False)


def setup_logger(name=None, level=logging.INFO, enable_json=False):
    """
    配置并返回logger实例

    Args:
        name: logger名称，默认为调用模块名
        level: 日志级别，默认INFO
        enable_json: 是否启用JSON格式，默认False

    Returns:
        配置好的logger实例
    """
    logger = logging.getLogger(name or __name__)

    # 避免重复添加handler
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # 添加请求ID过滤器
    request_id_filter = RequestIdFilter()

    # ===== 控制台处理器 =====
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(DETAILED_FORMAT, DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(request_id_filter)
    logger.addHandler(console_handler)

    # ===== 文件处理器 - 所有日志（轮转） =====
    all_log_file = os.path.join(LOG_DIR, 'all.log')
    # 最大10MB，保留5个备份文件
    all_file_handler = RotatingFileHandler(
        all_log_file,
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    all_file_handler.setLevel(logging.DEBUG)

    if enable_json:
        all_file_handler.setFormatter(StructuredFormatter())
    else:
        all_file_handler.setFormatter(logging.Formatter(DETAILED_FORMAT, DATE_FORMAT))

    all_file_handler.addFilter(request_id_filter)
    logger.addHandler(all_file_handler)

    # ===== 文件处理器 - 错误日志（轮转） =====
    error_log_file = os.path.join(LOG_DIR, 'error.log')
    error_file_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=10*1024*1024,
        backupCount=10,
        encoding='utf-8'
    )
    error_file_handler.setLevel(logging.ERROR)

    if enable_json:
        error_file_handler.setFormatter(StructuredFormatter())
    else:
        error_file_handler.setFormatter(logging.Formatter(DETAILED_FORMAT, DATE_FORMAT))

    error_file_handler.addFilter(request_id_filter)
    logger.addHandler(error_file_handler)

    # ===== 文件处理器 - 慢查询日志 =====
    slow_log_file = os.path.join(LOG_DIR, 'slow.log')
    slow_file_handler = RotatingFileHandler(
        slow_log_file,
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    slow_file_handler.setLevel(logging.WARNING)

    if enable_json:
        slow_file_handler.setFormatter(StructuredFormatter())
    else:
        slow_file_handler.setFormatter(logging.Formatter(DETAILED_FORMAT, DATE_FORMAT))

    slow_file_handler.addFilter(request_id_filter)
    # 这个handler只在需要时手动添加日志

    # ===== 文件处理器 - 性能监控日志（按天轮转） =====
    perf_log_file = os.path.join(LOG_DIR, 'performance.log')
    perf_file_handler = TimedRotatingFileHandler(
        perf_log_file,
        when='midnight',
        interval=1,
        backupCount=30,  # 保留30天
        encoding='utf-8'
    )
    perf_file_handler.setLevel(logging.INFO)
    perf_formatter = logging.Formatter(
        '%(asctime)s | %(request_id)s | %(operation)s | %(duration).3fs | %(message)s',
        DATE_FORMAT
    )
    perf_file_handler.setFormatter(perf_formatter)
    perf_file_handler.addFilter(request_id_filter)

    # 保存slow和perf handlers以供其他模块使用
    logger.slow_handler = slow_file_handler
    logger.perf_handler = perf_file_handler

    return logger


def set_request_id(request_id=None):
    """设置当前线程的请求ID"""
    _thread_local.request_id = request_id or str(uuid.uuid4())[:8]
    return _thread_local.request_id


def get_request_id():
    """获取当前线程的请求ID"""
    return getattr(_thread_local, 'request_id', 'NO-REQ-ID')


def clear_request_id():
    """清除当前线程的请求ID"""
    if hasattr(_thread_local, 'request_id'):
        delattr(_thread_local, 'request_id')


def log_function_call(logger=None, log_args=False):
    """
    装饰器：记录函数调用的详细信息

    Args:
        logger: 自定义logger
        log_args: 是否记录参数，默认False

    用法:
        @log_function_call()
        def my_function(arg1, arg2):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_logger = logger or logging.getLogger(func.__module__)
            func_name = f"{func.__module__}.{func.__name__}"

            # 记录函数调用开始
            if log_args:
                func_logger.debug(f"→ Calling {func_name}")
                func_logger.debug(f"  Args: {args}")
                func_logger.debug(f"  Kwargs: {kwargs}")
            else:
                func_logger.debug(f"→ Calling {func_name}")

            start_time = datetime.now()

            try:
                result = func(*args, **kwargs)

                # 记录函数调用成功
                elapsed = (datetime.now() - start_time).total_seconds()
                func_logger.debug(f"← {func_name} completed in {elapsed:.3f}s")

                # 记录慢查询
                if elapsed > SLOW_QUERY_THRESHOLD:
                    if hasattr(func_logger, 'slow_handler'):
                        func_logger.addHandler(func_logger.slow_handler)
                        func_logger.warning(
                            f"SLOW QUERY: {func_name} took {elapsed:.3f}s (threshold: {SLOW_QUERY_THRESHOLD}s)",
                            extra={'operation': func_name, 'duration': elapsed}
                        )
                        func_logger.removeHandler(func_logger.slow_handler)

                return result

            except Exception as e:
                # 记录函数调用失败
                elapsed = (datetime.now() - start_time).total_seconds()
                func_logger.error(f"✗ {func_name} failed after {elapsed:.3f}s")
                func_logger.error(f"  Error: {type(e).__name__}: {str(e)}")
                func_logger.debug(f"  Traceback:\n{traceback.format_exc()}")
                raise

        return wrapper
    return decorator


def log_api_request(operation_description=None, slow_threshold=None):
    """
    装饰器：记录API请求的详细信息（业务语义化）

    Args:
        operation_description: 操作描述
        slow_threshold: 慢API阈值，默认使用SLOW_API_THRESHOLD

    用法:
        @app.route('/api/example')
        @log_api_request("创建用户订单")
        def example_api():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from flask import request, session as flask_session

            func_logger = logging.getLogger(func.__module__)

            # 生成请求ID并设置到线程本地存储
            request_id = set_request_id()

            # 获取用户信息
            user_id = flask_session.get('user_id', 'anonymous')
            username = flask_session.get('username', 'anonymous')

            # 获取客户端IP
            client_ip = request.headers.get('X-Real-IP') or \
                       request.headers.get('X-Forwarded-For') or \
                       request.remote_addr

            # 提取关键业务参数
            business_params = {}
            if request.is_json:
                body = request.get_json() or {}
                for key, value in body.items():
                    if 'password' in key.lower() or 'token' in key.lower() or 'secret' in key.lower():
                        business_params[key] = '***HIDDEN***'
                    elif isinstance(value, (str, int, float, bool)):
                        business_params[key] = value
                    elif isinstance(value, dict):
                        business_params[key] = f"<dict:{len(value)}>"
                    elif isinstance(value, list):
                        business_params[key] = f"<list:{len(value)}>"

            # 获取路径参数
            path_params = {k: v for k, v in kwargs.items() if not k.startswith('_')}

            # 获取查询参数
            query_params = dict(request.args)

            # 构建操作描述
            operation = operation_description or f"{request.method} {func.__name__}"

            # ====== 请求开始日志 ======
            func_logger.info("╔" + "═" * 100 + "╗")
            func_logger.info(f"║ 【API请求】{operation}")
            func_logger.info(f"║ RequestID: {request_id} | User: {username}(ID:{user_id}) | IP: {client_ip}")
            func_logger.info(f"║ Endpoint: {request.method} {request.path}")
            func_logger.info(f"║ User-Agent: {request.headers.get('User-Agent', 'Unknown')[:80]}")

            if path_params:
                func_logger.info(f"║ 路径参数: {json.dumps(path_params, ensure_ascii=False)}")
            if query_params:
                func_logger.info(f"║ 查询参数: {json.dumps(query_params, ensure_ascii=False)}")
            if business_params:
                func_logger.info(f"║ 请求数据: {json.dumps(business_params, ensure_ascii=False)}")

            start_time = datetime.now()

            try:
                # 执行业务逻辑
                func_logger.info("║ ▶ 开始执行业务逻辑...")
                response = func(*args, **kwargs)

                # 解析响应
                elapsed = (datetime.now() - start_time).total_seconds()
                status = getattr(response, 'status_code', 200) if hasattr(response, 'status_code') else 200

                # 提取响应关键信息
                response_info = ""
                business_success = True
                if hasattr(response, 'get_json'):
                    try:
                        resp_data = response.get_json()
                        if isinstance(resp_data, dict):
                            if 'success' in resp_data:
                                business_success = resp_data.get('success', True)
                                response_info = f"success={business_success}"
                            if 'data' in resp_data and isinstance(resp_data['data'], dict):
                                response_info += f", data_keys={list(resp_data['data'].keys())}"
                            elif 'data' in resp_data and isinstance(resp_data['data'], list):
                                response_info += f", data_count={len(resp_data['data'])}"
                            if 'error' in resp_data:
                                response_info += f", error={resp_data.get('error')}"
                            if 'message' in resp_data:
                                response_info += f", message={resp_data.get('message')}"
                    except:
                        pass

                # ====== 请求完成日志 ======
                func_logger.info(f"║ ⏱ 执行完成: {elapsed:.3f}s | HTTP {status}")
                if response_info:
                    func_logger.info(f"║ 📤 响应: {response_info}")

                # 根据业务成功状态显示不同的图标
                if status >= 400 or not business_success:
                    func_logger.warning("║ ⚠ 请求失败")
                    func_logger.info("╚" + "═" * 100 + "╝")
                    func_logger.warning(f"[{operation}] 执行失败 (ReqID: {request_id})")
                else:
                    func_logger.info("║ ✓ 请求成功")
                    func_logger.info("╚" + "═" * 100 + "╝")
                    func_logger.info(f"[{operation}] 成功完成 (ReqID: {request_id})")

                # 记录性能数据
                if hasattr(func_logger, 'perf_handler'):
                    func_logger.addHandler(func_logger.perf_handler)
                    perf_msg = f"User={username} | Status={status} | Success={business_success}"
                    func_logger.info(
                        perf_msg,
                        extra={
                            'operation': operation,
                            'duration': elapsed,
                            'user_id': user_id
                        }
                    )
                    func_logger.removeHandler(func_logger.perf_handler)

                # 记录慢API
                threshold = slow_threshold or SLOW_API_THRESHOLD
                if elapsed > threshold:
                    if hasattr(func_logger, 'slow_handler'):
                        func_logger.addHandler(func_logger.slow_handler)
                        func_logger.warning(
                            f"🐌 SLOW API: {operation} took {elapsed:.3f}s (threshold: {threshold}s)",
                            extra={'operation': operation, 'duration': elapsed}
                        )
                        func_logger.removeHandler(func_logger.slow_handler)

                # 清除请求ID
                clear_request_id()

                return response

            except Exception as e:
                # ====== 请求失败日志 ======
                elapsed = (datetime.now() - start_time).total_seconds()
                func_logger.error(f"║ ✗ 执行异常: {elapsed:.3f}s")
                func_logger.error("╚" + "═" * 100 + "╝")
                func_logger.error(f"[{operation}] 执行异常 (ReqID: {request_id})")
                func_logger.error(f"异常类型: {type(e).__name__}")
                func_logger.error(f"异常信息: {str(e)}")
                func_logger.error(f"异常堆栈:\n{traceback.format_exc()}")

                # 清除请求ID
                clear_request_id()

                raise

        return wrapper
    return decorator


def log_service_call(operation_name, log_args=False):
    """
    装饰器：记录服务层操作

    Args:
        operation_name: 操作名称
        log_args: 是否记录参数

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
            req_id = get_request_id()
            func_logger.info(f"┌─ [Service] {operation_name} - 开始 (ReqID: {req_id})")

            if log_args:
                func_logger.debug(f"│  Function: {func.__name__}")
                # 只记录前3个参数，避免日志过长
                if args:
                    func_logger.debug(f"│  Args: {str(args)[:200]}")
                if kwargs:
                    func_logger.debug(f"│  Kwargs: {str(kwargs)[:200]}")

            start_time = datetime.now()

            try:
                result = func(*args, **kwargs)

                # 记录操作成功
                elapsed = (datetime.now() - start_time).total_seconds()
                func_logger.info(f"└─ [Service] {operation_name} - ✓ 完成 ({elapsed:.3f}s)")

                # 记录慢服务
                if elapsed > SLOW_QUERY_THRESHOLD:
                    if hasattr(func_logger, 'slow_handler'):
                        func_logger.addHandler(func_logger.slow_handler)
                        func_logger.warning(
                            f"SLOW SERVICE: {operation_name} took {elapsed:.3f}s",
                            extra={'operation': operation_name, 'duration': elapsed}
                        )
                        func_logger.removeHandler(func_logger.slow_handler)

                return result

            except Exception as e:
                # 记录操作失败
                elapsed = (datetime.now() - start_time).total_seconds()
                func_logger.error(f"└─ [Service] {operation_name} - ✗ 失败 ({elapsed:.3f}s)")
                func_logger.error(f"   Error: {type(e).__name__}: {str(e)}")
                func_logger.debug(f"   Traceback:\n{traceback.format_exc()}")
                raise

        return wrapper
    return decorator


def log_database_query(query_description):
    """
    装饰器：记录数据库查询

    用法:
        @log_database_query("查询用户列表")
        def get_users():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_logger = logging.getLogger(func.__module__)

            start_time = datetime.now()

            try:
                result = func(*args, **kwargs)
                elapsed = (datetime.now() - start_time).total_seconds()

                func_logger.debug(f"[DB] {query_description} - {elapsed:.3f}s")

                # 记录慢查询
                if elapsed > 1.0:  # 数据库查询超过1秒
                    if hasattr(func_logger, 'slow_handler'):
                        func_logger.addHandler(func_logger.slow_handler)
                        func_logger.warning(
                            f"SLOW DB QUERY: {query_description} took {elapsed:.3f}s",
                            extra={'operation': query_description, 'duration': elapsed}
                        )
                        func_logger.removeHandler(func_logger.slow_handler)

                return result

            except Exception as e:
                elapsed = (datetime.now() - start_time).total_seconds()
                func_logger.error(f"[DB] {query_description} - FAILED ({elapsed:.3f}s): {str(e)}")
                raise

        return wrapper
    return decorator


# 默认logger
default_logger = setup_logger('topn_platform')


# 导出常用函数
__all__ = [
    'setup_logger',
    'log_function_call',
    'log_api_request',
    'log_service_call',
    'log_database_query',
    'set_request_id',
    'get_request_id',
    'clear_request_id',
    'default_logger'
]
