#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查最新错误日志
"""
import paramiko

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

def check_error():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"Connecting to {SERVER_HOST}...")
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("Connected!\n")

        # 查看最新日志，特别是login_tester相关的
        print("="*80)
        print("Latest login test logs:")
        print("="*80)
        stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u topn -n 100 --no-pager | grep -A 5 -B 5 'login_tester\\|WebDriver\\|Chrome'")
        logs = stdout.read().decode('utf-8', errors='ignore')
        print(logs)

        # 尝试手动测试单进程模式
        print("\n" + "="*80)
        print("Testing WebDriver with single-process mode:")
        print("="*80)

        test_script = """
cd /home/u_topn/TOP_N/backend
/home/u_topn/TOP_N/venv/bin/python -c '
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--single-process")
options.binary_location = "/usr/bin/google-chrome"

try:
    driver = webdriver.Chrome(executable_path="/home/u_topn/chromedriver", options=options)
    print("SUCCESS: WebDriver started with single-process mode")
    driver.quit()
except Exception as e:
    print(f"FAILED: {e}")
'
"""
        stdin, stdout, stderr = ssh.exec_command(test_script, timeout=30)
        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')

        if output:
            print(output)
        if error:
            print("Error:", error)

        ssh.close()

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_error()
