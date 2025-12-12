#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查服务器运行日志
"""

import paramiko
import sys

# 服务器信息
SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"
APP_DIR = "/home/u_topn/TOP_N"

def check_server_logs():
    """检查服务器日志"""
    print("=" * 80)
    print("  连接服务器检查运行日志")
    print("=" * 80)

    try:
        # 创建SSH客户端
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        print(f"\n正在连接服务器 {SERVER_HOST}...")
        ssh.connect(
            hostname=SERVER_HOST,
            username=SERVER_USER,
            password=SERVER_PASSWORD,
            timeout=30
        )
        print("[OK] 连接成功")

        # 检查应用进程状态
        print("\n" + "=" * 80)
        print("1. 检查应用进程状态")
        print("=" * 80)
        stdin, stdout, stderr = ssh.exec_command("ps aux | grep 'gunicorn.*app' | grep -v grep")
        process_info = stdout.read().decode('utf-8', errors='ignore')
        if process_info.strip():
            print("[OK] 应用正在运行:")
            print(process_info)
        else:
            print("[FAIL] 应用未运行")

        # 检查Gunicorn错误日志
        print("\n" + "=" * 80)
        print("2. 检查 Gunicorn 错误日志 (最近50行)")
        print("=" * 80)
        stdin, stdout, stderr = ssh.exec_command(f"tail -n 50 {APP_DIR}/gunicorn_error.log")
        error_log = stdout.read().decode('utf-8', errors='ignore')
        if error_log.strip():
            print(error_log)
        else:
            print("(日志为空)")

        # 检查Gunicorn访问日志
        print("\n" + "=" * 80)
        print("3. 检查 Gunicorn 访问日志 (最近30行)")
        print("=" * 80)
        stdin, stdout, stderr = ssh.exec_command(f"tail -n 30 {APP_DIR}/gunicorn_access.log")
        access_log = stdout.read().decode('utf-8', errors='ignore')
        if access_log.strip():
            print(access_log)
        else:
            print("(日志为空)")

        # 检查应用目录文件
        print("\n" + "=" * 80)
        print("4. 检查应用目录文件")
        print("=" * 80)
        stdin, stdout, stderr = ssh.exec_command(f"ls -lh {APP_DIR}/backend/")
        file_list = stdout.read().decode('utf-8', errors='ignore')
        print(file_list)

        # 检查端口监听状态
        print("\n" + "=" * 80)
        print("5. 检查端口监听状态")
        print("=" * 80)
        stdin, stdout, stderr = ssh.exec_command("netstat -tuln | grep 8080")
        port_status = stdout.read().decode('utf-8', errors='ignore')
        if port_status.strip():
            print("[OK] 端口 8080 正在监听:")
            print(port_status)
        else:
            print("[FAIL] 端口 8080 未监听")

        # 测试API端点
        print("\n" + "=" * 80)
        print("6. 测试 API 端点")
        print("=" * 80)

        # 测试健康检查
        stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8080/health")
        health_response = stdout.read().decode('utf-8', errors='ignore')
        print("GET /health:")
        print(health_response)

        # 测试分析API (带详细错误)
        print("\nPOST /analyze (测试):")
        test_cmd = """curl -X POST http://localhost:8080/analyze \\
  -H "Content-Type: application/json" \\
  -d '{"text":"测试公司介绍"}' \\
  -v 2>&1"""
        stdin, stdout, stderr = ssh.exec_command(test_cmd)
        analyze_response = stdout.read().decode('utf-8', errors='ignore')
        print(analyze_response)

        ssh.close()
        print("\n" + "=" * 80)
        print("[OK] 日志检查完成")
        print("=" * 80)

    except Exception as e:
        print(f"\n[ERROR] 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = check_server_logs()
    sys.exit(0 if success else 1)
