#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复zhihu浏览器headless模式
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
    print("修复zhihu浏览器headless模式...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=10)

    # 上传文件
    sftp = ssh.open_sftp()
    local_file = PROJECT_ROOT / "backend" / "zhihu_auto_post_enhanced.py"
    remote_file = f"{DEPLOY_DIR}/backend/zhihu_auto_post_enhanced.py"

    print(f"上传: {local_file}")
    sftp.put(str(local_file), remote_file)
    print("✓ 已上传")
    sftp.close()

    # 重启服务
    print("\n重启服务...")
    stdin, stdout, stderr = ssh.exec_command("pkill -f gunicorn; sleep 2")
    stdout.read()

    start_cmd = f"bash {DEPLOY_DIR}/start_service.sh"
    stdin, stdout, stderr = ssh.exec_command(start_cmd)
    print(stdout.read().decode('utf-8', errors='ignore'))

    time.sleep(3)

    # 测试
    print("\n测试健康检查...")
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8080/api/health")
    print(stdout.read().decode('utf-8', errors='ignore'))

    print("\n✓ 完成")
    print("\n说明：")
    print("- 服务器环境会自动使用headless模式")
    print("- 本地环境（有显示器）会使用可见模式")

    ssh.close()

if __name__ == '__main__':
    main()
