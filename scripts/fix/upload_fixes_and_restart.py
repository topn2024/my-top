#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上传修复后的文件并重启服务
"""

import paramiko
import sys
import io
import time
from pathlib import Path

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

SERVER = "39.105.12.124"
USER = "u_topn"
PASSWORD = "TopN@2024"
DEPLOY_DIR = "/home/u_topn/TOP_N"

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def main():
    print("=" * 80)
    print("  上传修复文件并重启服务")
    print("=" * 80)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=10)
        print("✓ 已连接到服务器\n")

        sftp = ssh.open_sftp()

        # 上传修复的文件
        print("【1】上传修复后的文件")
        print("-" * 80)

        files_to_upload = [
            ("backend/blueprints/auth.py", "backend/blueprints/auth.py"),
            ("templates/platform.html", "templates/platform.html"),
        ]

        for local_path, remote_path in files_to_upload:
            local_file = PROJECT_ROOT / local_path
            remote_file = f"{DEPLOY_DIR}/{remote_path}"

            print(f"上传: {local_path}")
            sftp.put(str(local_file), remote_file)
            print(f"  ✓ 已上传到: {remote_file}")

        sftp.close()

        # 重启服务
        print("\n【2】重启服务")
        print("-" * 80)

        # 停止服务
        stdin, stdout, stderr = ssh.exec_command("pkill -f gunicorn")
        stdout.read()
        print("  停止旧服务...")
        time.sleep(2)

        # 启动服务
        stdin, stdout, stderr = ssh.exec_command(f"bash {DEPLOY_DIR}/start_service.sh")
        output = stdout.read().decode('utf-8', errors='ignore')
        print(output)

        # 等待启动
        print("  等待服务启动...")
        time.sleep(3)

        # 测试服务
        print("\n【3】测试服务")
        print("-" * 80)

        # 测试健康检查
        stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:3001/api/health")
        health = stdout.read().decode('utf-8', errors='ignore')
        print(f"健康检查: {health[:100]}")

        # 测试platform页面
        stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:3001/platform")
        platform_code = stdout.read().decode('utf-8', errors='ignore').strip()
        print(f"平台页面: HTTP {platform_code}")

        # 测试注册API
        stdin, stdout, stderr = ssh.exec_command(
            """curl -s -X POST -H 'Content-Type: application/json' -d '{"username":"testuser2","email":"test2@test.com","password":"test123"}' http://localhost:3001/api/auth/register"""
        )
        register_result = stdout.read().decode('utf-8', errors='ignore')
        print(f"注册API: {register_result[:150]}")

        # 测试首页
        stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:3001/")
        home_code = stdout.read().decode('utf-8', errors='ignore').strip()
        print(f"首页: HTTP {home_code}")

        # 总结
        print("\n" + "=" * 80)
        print("  修复完成!")
        print("=" * 80)

        if platform_code == "200" and "200" in home_code:
            print("\n✓ 所有测试通过!")
            print("\n请访问以下地址验证:")
            print(f"  主页: http://{SERVER}:3001")
            print(f"  平台页: http://{SERVER}:3001/platform")
            print(f"  登录页: http://{SERVER}:3001/login")
        else:
            print("\n⚠ 仍有问题需要检查")
            print(f"  平台页状态码: {platform_code}")
            print(f"  首页状态码: {home_code}")

    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == '__main__':
    main()
