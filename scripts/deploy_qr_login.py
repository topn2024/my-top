#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署知乎二维码登录功能
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

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def main():
    print("部署知乎二维码登录功能...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=10)

    # 上传文件
    sftp = ssh.open_sftp()

    files_to_upload = [
        ("backend/zhihu_qr_login.py", f"{DEPLOY_DIR}/backend/zhihu_qr_login.py"),
        ("backend/services/publish_service.py", f"{DEPLOY_DIR}/backend/services/publish_service.py"),
        ("backend/blueprints/api.py", f"{DEPLOY_DIR}/backend/blueprints/api.py"),
    ]

    print("\n上传文件...")
    for local_file, remote_file in files_to_upload:
        local_path = PROJECT_ROOT / local_file
        print(f"  上传: {local_file}")
        sftp.put(str(local_path), remote_file)

    print("✓ 所有文件已上传")
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

    print("\n✓ 部署完成")
    print("\n功能说明:")
    print("1. 当用户没有配置知乎账号时，发布会返回 requireQRLogin: true")
    print("2. 前端收到这个标记后，应该调用 POST /api/zhihu/qr_login/start 获取二维码")
    print("3. 显示二维码让用户扫码登录")
    print("4. 登录成功后保存Cookie，下次可以直接使用")

    ssh.close()

if __name__ == '__main__':
    main()
