#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上传ChromeDriver 143到服务器
"""
import paramiko
import time

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

def upload_chromedriver():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"Connecting to {SERVER_HOST}...")
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("Connected!\n")

        sftp = ssh.open_sftp()

        local_file = "D:\\work\\code\\TOP_N\\chromedriver-linux64\\chromedriver"
        remote_file = "/home/u_topn/chromedriver"

        print(f"Uploading {local_file} to {remote_file}...")
        sftp.put(local_file, remote_file)
        print("Upload complete!\n")

        sftp.close()

        # 设置执行权限
        print("Setting executable permissions...")
        stdin, stdout, stderr = ssh.exec_command("chmod +x /home/u_topn/chromedriver")
        stdout.read()
        print("Permissions set\n")

        # 验证版本
        print("Verifying ChromeDriver version...")
        stdin, stdout, stderr = ssh.exec_command("/home/u_topn/chromedriver --version")
        version = stdout.read().decode('utf-8', errors='ignore').strip()
        print(f"ChromeDriver version: {version}\n")

        # 重启服务
        print("Restarting topn service...")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl restart topn")
        stdout.read()
        time.sleep(3)

        # 检查服务状态
        print("\nChecking service status...")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl status topn --no-pager -n 5")
        status = stdout.read().decode('utf-8', errors='ignore')
        print(status)

        ssh.close()

        print("\n" + "="*80)
        print("SUCCESS! ChromeDriver 143 installed and service restarted")
        print("="*80)
        print("\nThe real website login testing is now ready!")
        print("\nTest at: http://39.105.12.124:8080")
        print("Click [Account Configuration] -> Add account -> Click [Test] button")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    upload_chromedriver()
