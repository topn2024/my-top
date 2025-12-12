#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查服务状态
"""

import paramiko
import sys
import io
import time

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

SERVER = "39.105.12.124"
USER = "u_topn"
PASSWORD = "TopN@2024"
DEPLOY_DIR = "/home/u_topn/TOP_N"

def execute(ssh, cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    return stdout.read().decode('utf-8', errors='ignore')

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=10)

    print("【1】检查进程")
    print(execute(ssh, "ps aux | grep gunicorn | grep -v grep || echo '无进程'"))

    print("\n【2】检查端口")
    print(execute(ssh, "ss -tlnp | grep :3001 || echo '端口未监听'"))

    print("\n【3】启动日志")
    print(execute(ssh, f"tail -30 {DEPLOY_DIR}/logs/startup.log || tail -30 {DEPLOY_DIR}/logs/error.log"))

    print("\n【4】手动启动")
    print("执行启动脚本...")
    execute(ssh, "pkill -f gunicorn; sleep 2")
    execute(ssh, f"bash {DEPLOY_DIR}/start_service.sh")
    time.sleep(3)

    print("\n【5】再次检查")
    print(execute(ssh, "ps aux | grep gunicorn | grep -v grep | wc -l"))
    print(execute(ssh, "curl -s http://localhost:3001/api/health || echo '无响应'"))

    ssh.close()

if __name__ == '__main__':
    main()
