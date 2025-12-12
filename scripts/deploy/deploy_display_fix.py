#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署DISPLAY环境变量修复
"""
import paramiko
import time

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

def deploy():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"Connecting to {SERVER_HOST}...")
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("Connected!\n")

        sftp = ssh.open_sftp()

        # 上传更新后的login_tester.py
        local_file = "D:\\work\\code\\TOP_N\\backend\\login_tester.py"
        remote_file = "/home/u_topn/TOP_N/backend/login_tester.py"

        print(f"Uploading {local_file}...")
        sftp.put(local_file, remote_file)
        print("Upload complete!\n")

        sftp.close()

        # 重启服务
        print("Restarting topn service...")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl restart topn")
        stdout.read()
        time.sleep(3)

        # 检查服务状态
        print("\nChecking service status...")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl status topn --no-pager -n 10")
        status = stdout.read().decode('utf-8', errors='ignore')
        print(status)

        # 测试WebDriver初始化
        print("\n" + "="*80)
        print("Testing WebDriver initialization with DISPLAY fix:")
        print("="*80)
        test_script = """
cd /home/u_topn/TOP_N/backend
/home/u_topn/TOP_N/venv/bin/python << 'EOF'
import sys
sys.path.insert(0, '/home/u_topn/TOP_N/backend')

from login_tester import LoginTester
import os

print(f"DISPLAY before init: {os.environ.get('DISPLAY', 'Not set')}")

tester = LoginTester(headless=True)
if tester.init_driver():
    print("SUCCESS: WebDriver initialized!")
    print(f"DISPLAY after init: {os.environ.get('DISPLAY', 'Not set')}")
    tester.close_driver()
else:
    print("FAILED: WebDriver initialization failed")
EOF
"""
        stdin, stdout, stderr = ssh.exec_command(test_script, timeout=60)
        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')

        if output:
            print(output)
        if error:
            print("Stderr:", error)

        ssh.close()

        print("\n" + "="*80)
        print("DEPLOYMENT COMPLETE!")
        print("="*80)
        print("\nThe DISPLAY environment variable fix has been deployed.")
        print("WebDriver should now initialize correctly in the systemd service.")
        print("\nTest at: http://39.105.12.124:8080")
        print("Go to [Account Configuration] -> Add account -> Click [Test] button")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    deploy()
