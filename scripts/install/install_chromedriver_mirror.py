#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用国内镜像安装ChromeDriver
"""
import paramiko
import time

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

def install_chromedriver():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"Connecting to {SERVER_HOST}...")
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("Connected!\n")

        # 使用淘宝镜像或直接下载较老版本的chromedriver
        # Chrome 143 可以用 ChromeDriver 114-120 之间的版本
        commands = [
            ("Change to home directory", "cd /home/u_topn"),
            ("Remove old files", "rm -f chromedriver*"),
            # 使用淘宝NPM chromedriver镜像
            ("Download ChromeDriver from Taobao mirror",
             "wget https://registry.npmmirror.com/-/binary/chromedriver/114.0.5735.90/chromedriver_linux64.zip"),
            ("Unzip chromedriver", "unzip -o chromedriver_linux64.zip"),
            ("Make executable", "chmod +x /home/u_topn/chromedriver"),
            ("Verify installation", "/home/u_topn/chromedriver --version"),
            ("Clean up zip", "rm -f chromedriver_linux64.zip"),
        ]

        for step_name, cmd in commands:
            print(f"{'='*60}")
            print(f"{step_name}")
            print('='*60)

            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
            output = stdout.read().decode('utf-8', errors='ignore').strip()
            error = stderr.read().decode('utf-8', errors='ignore').strip()

            if output:
                print(f"{output}")
            if error and "saving to" not in error.lower():
                if "warning" not in error.lower():
                    print(f"Error: {error}")

            print("[OK]\n")
            time.sleep(0.5)

        # 上传更新后的login_tester.py
        print("="*60)
        print("Uploading updated login_tester.py")
        print("="*60)

        sftp = ssh.open_sftp()
        sftp.put("D:\\work\\code\\TOP_N\\backend\\login_tester.py", "/home/u_topn/TOP_N/backend/login_tester.py")
        sftp.close()
        print("[OK]\n")

        # 重启服务
        print("="*60)
        print("Restarting service")
        print("="*60)
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl restart topn")
        stdout.read()
        time.sleep(3)

        print("\nChecking service status...")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl status topn --no-pager -n 5")
        status = stdout.read().decode('utf-8', errors='ignore')
        print(status)

        ssh.close()

        print("\n" + "="*80)
        print("ChromeDriver installation complete!")
        print("="*80)
        print("\nChromeDriver installed at: /home/u_topn/chromedriver")
        print("login_tester.py updated to use explicit chromedriver path")
        print("\nPlease test at: http://39.105.12.124:8080")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    install_chromedriver()
