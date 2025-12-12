#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署模块化登录系统
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
    print("部署模块化登录系统...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=10)

    # 创建zhihu_auth目录
    print("\n创建zhihu_auth目录...")
    sftp = ssh.open_sftp()
    try:
        sftp.mkdir(f"{DEPLOY_DIR}/backend/zhihu_auth")
    except:
        print("zhihu_auth目录已存在")

    # 上传文件
    files_to_upload = [
        ("backend/zhihu_auth/__init__.py", f"{DEPLOY_DIR}/backend/zhihu_auth/__init__.py"),
        ("backend/zhihu_auth/zhihu_cookie_login.py", f"{DEPLOY_DIR}/backend/zhihu_auth/zhihu_cookie_login.py"),
        ("backend/zhihu_auth/zhihu_password_login.py", f"{DEPLOY_DIR}/backend/zhihu_auth/zhihu_password_login.py"),
        ("backend/zhihu_auth/zhihu_qr_login.py", f"{DEPLOY_DIR}/backend/zhihu_auth/zhihu_qr_login.py"),
        ("backend/blueprints/api.py", f"{DEPLOY_DIR}/backend/blueprints/api.py"),
        ("static/publish.js", f"{DEPLOY_DIR}/static/publish.js"),
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
    print("\n模块说明:")
    print("1. ZhihuCookieLogin - Cookie登录模块（加载已保存的Cookie）")
    print("2. ZhihuPasswordLogin - 密码登录模块（使用账号密码登录）")
    print("3. ZhihuQRLogin - 二维码登录模块（扫码登录）")
    print("\n前端功能:")
    print("1. 发布时如果没有配置账号，会自动弹出二维码")
    print("2. 用户扫码登录后，自动保存Cookie并继续发布")
    print("3. 下次发布时可以直接使用Cookie登录")

    ssh.close()

if __name__ == '__main__':
    main()
