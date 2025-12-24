#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化版日志配置模块
提供清晰、易读的日志输出，便于问题定位和性能监控

日志格式设计原则:
1. 一行一条日志，便于grep和快速扫描
2. 关键信息前置：时间 > 级别 > 模块 > 消息
3. 使用颜色区分级别（控制台）
4. 敏感信息自动脱敏
5. 请求链路追踪（RequestID）
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
import re

# 线程本地存储，用于存储请求ID
_thread_local = local()

# 日志目录
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# 慢操作阈值（秒）
SLOW_QUERY_THRESHOLD = 3.0
SLOW_API_THRESHOLD = 2.0


# ============================================================
# 颜色定义（控制台输出）
# ============================================================
class LogColors:
    """日志颜色代码"""
    RESET = '\033[0m'
    BOLD = '\033[1m'

    # 级别颜色
    DEBUG = '\033[36m'      # 青色
    INFO = '\033[32m'       # 绿色
    WARNING = '\033[33m'    # 黄色
    ERROR = '\033[31m'      # 红色
    CRITICAL = '\033[35m'   # 紫色

    # 特殊颜色
    TIME = '\033[90m'       # 灰色
    MODULE = '\033[34m'     # 蓝色
    REQUEST_ID = '\033[95m' # 亮紫色


class RequestIdFilter(logging.Filter):
    """为日志添加请求ID"""
    def filter(self, record):
        record.request_id = getattr(_thread_local, 'request_id', '-')
        return True


# ============================================================
# 日志格式化器
# ============================================================
class CompactFormatter(logging.Formatter):
    """紧凑型格式化器 - 用于文件日志"""

    def __init__(self):
        # 格式: 时间 | 级别 | 请求ID | 模块:行号 | 消息
        fmt = '%(asctime)s | %(levelname)-5s | %(request_id)-8s | %(name)-20s | %(message)s'
        super().__init__(fmt, datefmt='%Y-%m-%d %H:%M:%S')


class ColoredFormatter(logging.Formatter):
    """彩色格式化器 - 用于控制台日志"""

    LEVEL_COLORS = {
        logging.DEBUG: LogColors.DEBUG,
        logging.INFO: LogColors.INFO,
        logging.WARNING: LogColors.WARNING,
        logging.ERROR: LogColors.ERROR,
        logging.CRITICAL: LogColors.CRITICAL,
    }

    def format(self, record):
        # 获取级别颜色
        level_color = self.LEVEL_COLORS.get(record.levelno, LogColors.RESET)

        # 格式化时间（灰色）
        time_str = f"{LogColors.TIME}{datetime.fromtimestamp(record.created).strftime('%H:%M:%S')}{LogColors.RESET}"

        # 格式化级别（彩色）
        level_str = f"{level_color}{record.levelname:5}{LogColors.RESET}"

        # 格式化请求ID（亮紫色）
        req_id = getattr(record, 'request_id', '-')
        req_id_str = f"{LogColors.REQUEST_ID}{req_id:8}{LogColors.RESET}" if req_id != '-' else f"{'':8}"

        # 格式化模块名（蓝色，截断到20字符）
        module_name = record.name[:20] if len(record.name) > 20 else record.name
        module_str = f"{LogColors.MODULE}{module_name:20}{LogColors.RESET}"

        # 格式化消息
        message = record.getMessage()

        # 如果是错误，添加红色
        if record.levelno >= logging.ERROR:
            message = f"{LogColors.ERROR}{message}{LogColors.RESET}"

        # 组合输出
        formatted = f"{time_str} {level_str} {req_id_str} {module_str} {message}"

        # 添加异常信息
        if record.exc_info:
            formatted += f"\n{LogColors.ERROR}{self.formatException(record.exc_info)}{LogColors.RESET}"

        return formatted


class JSONFormatter(logging.Formatter):
    """JSON格式化器 - 用于日志分析系统"""

    def format(self, record):
        log_data = {
            'ts': datetime.fromtimestamp(record.created).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3],
            'level': record.levelname,
            'logger': record.name,
            'req_id': getattr(record, 'request_id', '-'),
            'msg': record.getMessage(),
        }

        # 添加额外字段
        for key in ['user', 'duration', 'status', 'method', 'path', 'ip']:
            if hasattr(record, key):
                log_data[key] = getattr(record, key)

        # 添加异常信息
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


# ============================================================
# Logger配置
# ============================================================
def setup_logger(name=None, level=logging.INFO, enable_json=False):
    """
    配置并返回logger实例

    Args:
        name: logger名称
        level: 日志级别
        enable_json: 是否启用JSON格式（用于日志分析系统）

    Returns:
        配置好的logger实例
    """
    logger = logging.getLogger(name or __name__)

    # 避免重复添加handler
    if logger.handlers:
        return logger

    logger.setLevel(level)
    logger.propagate = False  # 避免重复输出

    # 添加请求ID过滤器
    request_id_filter = RequestIdFilter()

    # ===== 控制台处理器（彩色输出）=====
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(ColoredFormatter())
    console_handler.addFilter(request_id_filter)
    logger.addHandler(console_handler)

    # ===== 文件处理器 - 所有日志 =====
    all_log_file = os.path.join(LOG_DIR, 'all.log')
    all_handler = RotatingFileHandler(
        all_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    all_handler.setLevel(logging.DEBUG)
    all_handler.setFormatter(JSONFormatter() if enable_json else CompactFormatter())
    all_handler.addFilter(request_id_filter)
    logger.addHandler(all_handler)

    # ===== 文件处理器 - 错误日志 =====
    error_log_file = os.path.join(LOG_DIR, 'error.log')
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=10*1024*1024,
        backupCount=10,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(CompactFormatter())
    error_handler.addFilter(request_id_filter)
    logger.addHandler(error_handler)

    return logger


# ============================================================
# 请求ID管理
# ============================================================
def set_request_id(request_id=None):
    """设置当前线程的请求ID"""
    _thread_local.request_id = request_id or str(uuid.uuid4())[:8]
    return _thread_local.request_id


def get_request_id():
    """获取当前线程的请求ID"""
    return getattr(_thread_local, 'request_id', '-')


def clear_request_id():
    """清除当前线程的请求ID"""
    if hasattr(_thread_local, 'request_id'):
        delattr(_thread_local, 'request_id')


# ============================================================
# 敏感信息脱敏
# ============================================================
SENSITIVE_KEYS = {'password', 'passwd', 'pwd', 'token', 'secret', 'api_key', 'apikey', 'authorization'}
SENSITIVE_PATTERN = re.compile(r'(password|passwd|pwd|token|secret|api_key|apikey)[\s]*[=:]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE)

def mask_sensitive(data):
    """脱敏敏感信息"""
    if isinstance(data, dict):
        return {
            k: '***' if k.lower() in SENSITIVE_KEYS else mask_sensitive(v)
            for k, v in data.items()
        }
    elif isinstance(data, str):
        return SENSITIVE_PATTERN.sub(r'\1=***', data)
    elif isinstance(data, list):
        return [mask_sensitive(item) for item in data]
    return data


def summarize_data(data, max_len=100):
    """摘要化数据，避免日志过长"""
    if isinstance(data, dict):
        keys = list(data.keys())
        return f"{{keys={keys[:5]}{'...' if len(keys) > 5 else ''}, len={len(data)}}}"
    elif isinstance(data, list):
        return f"[len={len(data)}]"
    elif isinstance(data, str) and len(data) > max_len:
        return f"{data[:max_len]}...(len={len(data)})"
    return data


# ============================================================
# 装饰器 - API请求日志
# ============================================================
def log_api_request(operation=None, slow_threshold=None):
    """
    装饰器：记录API请求（单行格式）

    Args:
        operation: 操作描述（如"用户登录"）
        slow_threshold: 慢API阈值（秒）

    用法:
        @app.route('/api/login')
        @log_api_request("用户登录")
        def login():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from flask import request, session as flask_session

            # 获取或创建logger
            logger = logging.getLogger(func.__module__)
            if not logger.handlers:
                logger = setup_logger(func.__module__)

            # 生成请求ID
            req_id = set_request_id()

            # 获取请求信息
            method = request.method
            path = request.path
            user = flask_session.get('username', '-')
            ip = request.headers.get('X-Real-IP') or request.headers.get('X-Forwarded-For') or request.remote_addr

            # 操作名称
            op_name = operation or f"{method} {func.__name__}"

            # 记录请求开始（单行）
            logger.info(
                f">>> {op_name} | {method} {path} | user={user} ip={ip}",
                extra={'user': user, 'method': method, 'path': path, 'ip': ip}
            )

            start_time = datetime.now()

            try:
                # 执行业务逻辑
                response = func(*args, **kwargs)

                # 计算耗时
                duration = (datetime.now() - start_time).total_seconds()

                # 获取响应状态
                status = getattr(response, 'status_code', 200)

                # 判断是否成功
                success = True
                msg = ""
                if hasattr(response, 'get_json'):
                    try:
                        resp_data = response.get_json()
                        if isinstance(resp_data, dict):
                            success = resp_data.get('success', True)
                            if 'error' in resp_data:
                                msg = f" error={resp_data['error']}"
                            elif 'message' in resp_data:
                                msg = f" msg={resp_data['message'][:50]}"
                    except:
                        pass

                # 记录请求完成（单行）
                status_icon = "OK" if status < 400 and success else "FAIL"
                log_msg = f"<<< {op_name} | {status_icon} {status} | {duration:.3f}s{msg}"

                if status >= 400 or not success:
                    logger.warning(log_msg, extra={'status': status, 'duration': duration})
                elif duration > (slow_threshold or SLOW_API_THRESHOLD):
                    logger.warning(f"<<< {op_name} | SLOW {status} | {duration:.3f}s (>{slow_threshold or SLOW_API_THRESHOLD}s){msg}",
                                 extra={'status': status, 'duration': duration})
                else:
                    logger.info(log_msg, extra={'status': status, 'duration': duration})

                clear_request_id()
                return response

            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                logger.error(
                    f"<<< {op_name} | ERROR | {duration:.3f}s | {type(e).__name__}: {str(e)[:100]}",
                    extra={'status': 500, 'duration': duration}
                )
                logger.debug(f"Traceback:\n{traceback.format_exc()}")
                clear_request_id()
                raise

        return wrapper
    return decorator


# ============================================================
# 装饰器 - 服务层日志
# ============================================================
def log_service_call(operation, log_args=False):
    """
    装饰器：记录服务层调用

    Args:
        operation: 操作名称
        log_args: 是否记录参数
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            if not logger.handlers:
                logger = setup_logger(func.__module__)

            req_id = get_request_id()

            # 记录开始
            if log_args and kwargs:
                params = summarize_data(mask_sensitive(kwargs))
                logger.debug(f"[SVC] {operation} start | params={params}")
            else:
                logger.debug(f"[SVC] {operation} start")

            start_time = datetime.now()

            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()

                if duration > SLOW_QUERY_THRESHOLD:
                    logger.warning(f"[SVC] {operation} done | {duration:.3f}s (SLOW)")
                else:
                    logger.debug(f"[SVC] {operation} done | {duration:.3f}s")

                return result

            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                logger.error(f"[SVC] {operation} fail | {duration:.3f}s | {type(e).__name__}: {str(e)[:80]}")
                raise

        return wrapper
    return decorator


# ============================================================
# 装饰器 - 数据库查询日志
# ============================================================
def log_database_query(description):
    """装饰器：记录数据库查询"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            if not logger.handlers:
                logger = setup_logger(func.__module__)

            start_time = datetime.now()

            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()

                if duration > 1.0:
                    logger.warning(f"[DB] {description} | {duration:.3f}s (SLOW)")
                else:
                    logger.debug(f"[DB] {description} | {duration:.3f}s")

                return result

            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                logger.error(f"[DB] {description} | FAIL {duration:.3f}s | {type(e).__name__}")
                raise

        return wrapper
    return decorator


# ============================================================
# 便捷函数
# ============================================================
def log_function_call(logger=None, log_args=False):
    """装饰器：记录函数调用（用于调试）"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_logger = logger or logging.getLogger(func.__module__)
            func_name = f"{func.__module__}.{func.__name__}"

            func_logger.debug(f"-> {func_name}")
            start = datetime.now()

            try:
                result = func(*args, **kwargs)
                elapsed = (datetime.now() - start).total_seconds()
                func_logger.debug(f"<- {func_name} | {elapsed:.3f}s")
                return result
            except Exception as e:
                elapsed = (datetime.now() - start).total_seconds()
                func_logger.error(f"<- {func_name} | FAIL {elapsed:.3f}s | {e}")
                raise

        return wrapper
    return decorator


# 默认logger
default_logger = setup_logger('topn')


# ============================================================
# 结构化错误日志
# ============================================================
def log_error(logger_instance, error_code: str, message: str,
              exception: Exception = None, extra_data: dict = None):
    """
    记录结构化错误日志

    Args:
        logger_instance: logger实例
        error_code: 错误码 (如 ERR-10001)
        message: 错误描述
        exception: 原始异常对象
        extra_data: 额外数据

    用法:
        from logger_config import log_error, default_logger
        log_error(default_logger, 'ERR-10001', '用户登录失败', exception=e)
    """
    try:
        from error_codes import classify_error

        # 获取异常类型
        exc_type = type(exception).__name__ if exception else None

        # 分类错误
        error_info = classify_error(message, exc_type)

        # 构建日志消息
        log_parts = [
            f"[{error_code or error_info['code']}]",
            f"[{error_info['category']}]",
            f"{error_info['name']}:",
            message
        ]

        if exception:
            log_parts.append(f"| {exc_type}: {str(exception)[:100]}")

        log_msg = ' '.join(log_parts)

        # 根据严重级别选择日志方法
        severity = error_info.get('severity', 'ERROR')
        extra = {
            'error_code': error_code or error_info['code'],
            'category': error_info['category'],
            'severity': severity,
            **(extra_data or {})
        }

        if severity == 'CRITICAL':
            logger_instance.critical(log_msg, extra=extra, exc_info=exception is not None)
        elif severity == 'WARNING':
            logger_instance.warning(log_msg, extra=extra)
        else:
            logger_instance.error(log_msg, extra=extra)

    except ImportError:
        # error_codes模块未加载时的回退
        if exception:
            logger_instance.error(f"[{error_code}] {message} | {type(exception).__name__}: {exception}")
        else:
            logger_instance.error(f"[{error_code}] {message}")


def log_business_error(operation: str, error_type: str, message: str,
                       user: str = None, extra: dict = None):
    """
    记录业务错误（用于业务层）

    Args:
        operation: 操作名称
        error_type: 错误类型 (AUTH/BIZ/VALID/EXT/SYS/RES/NET/DB)
        message: 错误消息
        user: 用户标识
        extra: 额外信息
    """
    log_data = {
        'operation': operation,
        'type': error_type,
        'message': message
    }
    if user:
        log_data['user'] = user
    if extra:
        log_data.update(extra)

    default_logger.error(
        f"[BIZ-ERROR] {operation} | type={error_type} | {message}",
        extra=log_data
    )


def log_external_error(service: str, operation: str, status_code: int = None,
                       response: str = None, duration: float = None):
    """
    记录外部服务调用错误

    Args:
        service: 服务名称 (如 'openai', 'zhihu', 'weixin')
        operation: 操作名称
        status_code: HTTP状态码
        response: 响应内容
        duration: 耗时（秒）
    """
    parts = [f"[EXT-ERROR] {service}.{operation}"]

    if status_code:
        parts.append(f"status={status_code}")
    if duration:
        parts.append(f"took={duration:.3f}s")
    if response:
        parts.append(f"resp={response[:100]}")

    default_logger.error(' | '.join(parts))


def log_db_error(operation: str, table: str = None, error: Exception = None):
    """
    记录数据库错误

    Args:
        operation: 操作类型 (SELECT/INSERT/UPDATE/DELETE)
        table: 表名
        error: 异常对象
    """
    parts = [f"[DB-ERROR] {operation}"]
    if table:
        parts.append(f"table={table}")
    if error:
        parts.append(f"{type(error).__name__}: {str(error)[:100]}")

    default_logger.error(' | '.join(parts))


# 导出
__all__ = [
    'setup_logger',
    'log_api_request',
    'log_service_call',
    'log_database_query',
    'log_function_call',
    'log_error',
    'log_business_error',
    'log_external_error',
    'log_db_error',
    'set_request_id',
    'get_request_id',
    'clear_request_id',
    'mask_sensitive',
    'default_logger'
]
