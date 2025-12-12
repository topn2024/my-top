#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gunicorn 配置文件
用于生产环境部署
"""

import multiprocessing
import os

# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 绑定地址和端口
bind = "0.0.0.0:3001"

# 工作进程数 (建议设置为 CPU 核心数的 2-4 倍)
workers = multiprocessing.cpu_count() * 2 + 1
# 最大工作进程数限制
if workers > 8:
    workers = 8

# 工作模式
worker_class = "sync"

# 每个 worker 的线程数
threads = 2

# 超时时间(秒)
timeout = 120

# 保持连接时间(秒)
keepalive = 5

# 最大请求数,之后重启 worker (防止内存泄漏)
max_requests = 1000
max_requests_jitter = 50

# 守护进程
daemon = False

# PID 文件
pidfile = os.path.join(BASE_DIR, "logs", "gunicorn.pid")

# 日志文件
accesslog = os.path.join(BASE_DIR, "logs", "gunicorn_access.log")
errorlog = os.path.join(BASE_DIR, "logs", "gunicorn_error.log")

# 日志级别
loglevel = "info"

# 访问日志格式
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 进程名称
proc_name = "topn_gunicorn"

# 预加载应用 (节省内存,但更新代码需要重启所有 worker)
preload_app = False

# 工作目录
chdir = BASE_DIR

# 环境变量
raw_env = [
    'FLASK_ENV=production',
    'PYTHONPATH=%s' % BASE_DIR,
]

# 优雅重启超时
graceful_timeout = 30

# 临时文件目录
worker_tmp_dir = "/dev/shm"  # 使用内存文件系统,提高性能

# SSL (如果需要)
# keyfile = None
# certfile = None

# 钩子函数

def on_starting(server):
    """服务器启动时"""
    print("=" * 60)
    print("TOP_N 服务启动中...")
    print(f"工作目录: {BASE_DIR}")
    print(f"绑定地址: {bind}")
    print(f"工作进程: {workers}")
    print("=" * 60)

def on_reload(server):
    """重新加载配置时"""
    print("重新加载配置...")

def when_ready(server):
    """服务器准备就绪时"""
    print("✓ 服务器已准备就绪")
    print(f"✓ PID 文件: {pidfile}")
    print(f"✓ 访问日志: {accesslog}")
    print(f"✓ 错误日志: {errorlog}")

def pre_fork(server, worker):
    """Fork worker 之前"""
    pass

def post_fork(server, worker):
    """Fork worker 之后"""
    print(f"Worker {worker.pid} 已启动")

def pre_exec(server):
    """重新执行之前"""
    print("重新执行服务器...")

def worker_int(worker):
    """Worker 收到 SIGINT 信号"""
    print(f"Worker {worker.pid} 收到中断信号")

def worker_abort(worker):
    """Worker 收到 SIGABRT 信号"""
    print(f"Worker {worker.pid} 异常终止")

def on_exit(server):
    """服务器退出时"""
    print("=" * 60)
    print("TOP_N 服务已停止")
    print("=" * 60)
