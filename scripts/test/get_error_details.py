#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取错误详情
"""

import paramiko
import sys
import io

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

SERVER = "39.105.12.124"
USER = "u_topn"
PASSWORD = "TopN@2024"
DEPLOY_DIR = "/home/u_topn/TOP_N"

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=10)

    print("=" * 80)
    print("  获取错误详情")
    print("=" * 80)

    # 1. 测试 /platform 页面并查看错误
    print("\n【1】测试 /platform 页面")
    print("-" * 80)
    stdin, stdout, stderr = ssh.exec_command(
        "curl -s http://localhost:3001/platform 2>&1; sleep 1; tail -50 /home/u_topn/TOP_N/logs/error.log | grep -A 20 platform"
    )
    print(stdout.read().decode('utf-8', errors='ignore'))

    # 2. 测试注册API并查看错误
    print("\n【2】测试注册API")
    print("-" * 80)
    stdin, stdout, stderr = ssh.exec_command(
        """curl -s -X POST -H 'Content-Type: application/json' -d '{"username":"testuser","email":"test@test.com","password":"test123"}' http://localhost:3001/api/auth/register; sleep 1; tail -50 /home/u_topn/TOP_N/logs/error.log | grep -A 20 register"""
    )
    print(stdout.read().decode('utf-8', errors='ignore'))

    # 3. 查看完整的最新错误日志
    print("\n【3】最新错误日志")
    print("-" * 80)
    stdin, stdout, stderr = ssh.exec_command(
        f"tail -100 {DEPLOY_DIR}/logs/error.log"
    )
    print(stdout.read().decode('utf-8', errors='ignore'))

    ssh.close()

if __name__ == '__main__':
    main()
