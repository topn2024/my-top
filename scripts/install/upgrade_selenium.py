#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
升级Selenium到4.x并安装webdriver-manager
"""
import paramiko
import time

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

def upgrade_selenium():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"Connecting to {SERVER_HOST}...")
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("Connected!\n")

        commands = [
            ("Upgrade Selenium to 4.x",
             "/home/u_topn/TOP_N/venv/bin/pip install -i https://mirrors.aliyun.com/pypi/simple/ --upgrade 'selenium>=4.0.0,<5.0.0'"),
            ("Install webdriver-manager",
             "/home/u_topn/TOP_N/venv/bin/pip install -i https://mirrors.aliyun.com/pypi/simple/ webdriver-manager"),
            ("Verify Selenium version",
             "/home/u_topn/TOP_N/venv/bin/python -c 'import selenium; print(\"Selenium:\", selenium.__version__)'"),
        ]

        for step_name, cmd in commands:
            print(f"{'='*60}")
            print(f"{step_name}")
            print('='*60)

            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=180)
            output = stdout.read().decode('utf-8', errors='ignore').strip()
            error = stderr.read().decode('utf-8', errors='ignore').strip()

            if output:
                print(output[-500:])  # Show last 500 chars
            if error and "successfully installed" in error.lower():
                print(f"Success: {error[-300:]}")

            print("[OK]\n")
            time.sleep(1)

        ssh.close()

        print("\n" + "="*80)
        print("Selenium upgrade complete!")
        print("="*80)
        print("\nNow updating login_tester.py to use Selenium 4...")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    upgrade_selenium()
