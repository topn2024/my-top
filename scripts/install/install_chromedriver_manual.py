#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动安装ChromeDriver到用户home目录
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

        # 下载ChromeDriver到home目录（不需要sudo权限）
        commands = [
            ("Change to home directory", "cd /home/u_topn"),
            ("Remove old chromedriver files", "rm -f chromedriver chromedriver.zip chromedriver_linux64.zip"),
            ("Download ChromeDriver using curl", "curl -L -o chromedriver.zip https://storage.googleapis.com/chrome-for-testing-public/131.0.6778.204/linux64/chromedriver-linux64.zip"),
            ("Unzip chromedriver", "unzip -o chromedriver.zip"),
            ("Move binary to home", "mv chromedriver-linux64/chromedriver /home/u_topn/chromedriver"),
            ("Make executable", "chmod +x /home/u_topn/chromedriver"),
            ("Verify installation", "/home/u_topn/chromedriver --version"),
            ("Clean up", "rm -rf chromedriver-linux64 chromedriver.zip"),
        ]

        for step_name, cmd in commands:
            print(f"{'='*60}")
            print(f"{step_name}")
            print(f"Command: {cmd}")
            print('='*60)

            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
            output = stdout.read().decode('utf-8', errors='ignore').strip()
            error = stderr.read().decode('utf-8', errors='ignore').strip()

            if output:
                print(f"Output: {output}")
            if error and "warning" not in error.lower() and "inflating" not in error.lower():
                print(f"Error: {error}")

            print("[OK]\n")
            time.sleep(0.5)

        ssh.close()

        print("\n" + "="*80)
        print("ChromeDriver installed to /home/u_topn/chromedriver")
        print("="*80)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    install_chromedriver()
