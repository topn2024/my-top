#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动上传ChromeDriver 143到服务器
需要先在本地下载ChromeDriver 143
"""
import paramiko
import time
import os
import urllib.request
import zipfile

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

def upload_chromedriver():
    # 首先下载ChromeDriver 143
    chromedriver_url = "https://storage.googleapis.com/chrome-for-testing-public/143.0.7498.0/linux64/chromedriver-linux64.zip"
    local_zip = "D:\\work\\code\\TOP_N\\chromedriver-linux64.zip"
    local_binary = "D:\\work\\code\\TOP_N\\chromedriver"

    print(f"Downloading ChromeDriver 143 from {chromedriver_url}...")
    try:
        urllib.request.urlretrieve(chromedriver_url, local_zip)
        print(f"Downloaded to {local_zip}")

        # 解压
        print("Extracting...")
        with zipfile.ZipFile(local_zip, 'r') as zip_ref:
            zip_ref.extractall("D:\\work\\code\\TOP_N\\")

        # 找到解压出来的chromedriver
        extracted_path = "D:\\work\\code\\TOP_N\\chromedriver-linux64\\chromedriver"
        if os.path.exists(extracted_path):
            print(f"Found chromedriver at {extracted_path}")
            # 复制到临时位置
            import shutil
            shutil.copy(extracted_path, local_binary)
            print(f"Copied to {local_binary}")
        else:
            print(f"ERROR: Could not find chromedriver at {extracted_path}")
            return

    except Exception as e:
        print(f"Download/extract failed: {e}")
        print("Please manually download ChromeDriver 143 from:")
        print("https://storage.googleapis.com/chrome-for-testing-public/143.0.7498.0/linux64/chromedriver-linux64.zip")
        print(f"Extract and place it at: {local_binary}")
        if not os.path.exists(local_binary):
            return

    # 现在上传到服务器
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"\nConnecting to {SERVER_HOST}...")
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("Connected!\n")

        sftp = ssh.open_sftp()

        print("Uploading chromedriver to server...")
        sftp.put(local_binary, "/home/u_topn/chromedriver")
        print("Upload complete")

        sftp.close()

        # 设置权限
        print("Setting executable permissions...")
        stdin, stdout, stderr = ssh.exec_command("chmod +x /home/u_topn/chromedriver")
        stdout.read()

        # 验证
        print("\nVerifying ChromeDriver...")
        stdin, stdout, stderr = ssh.exec_command("/home/u_topn/chromedriver --version")
        version = stdout.read().decode('utf-8', errors='ignore').strip()
        print(f"ChromeDriver version: {version}")

        # 重启服务
        print("\nRestarting service...")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl restart topn")
        stdout.read()
        time.sleep(3)

        # 查看状态
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl status topn --no-pager -n 3")
        status = stdout.read().decode('utf-8', errors='ignore')
        print(status)

        ssh.close()

        print("\n" + "="*80)
        print("ChromeDriver 143 uploaded successfully!")
        print("="*80)
        print("\nPlease test at: http://39.105.12.124:8080")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    upload_chromedriver()
