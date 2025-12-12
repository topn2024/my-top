#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试WebDriver初始化
"""
import paramiko

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

def test_webdriver():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"Connecting to {SERVER_HOST}...")
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("Connected!\n")

        test_script = """
cd /home/u_topn/TOP_N
/home/u_topn/TOP_N/venv/bin/python << 'EOF'
import sys
sys.path.insert(0, '/home/u_topn/TOP_N/backend')

from login_tester import LoginTester

print("Testing WebDriver initialization...")
tester = LoginTester(headless=True)

if tester.init_driver():
    print("[SUCCESS] WebDriver initialized successfully!")
    print(f"Driver info: {tester.driver.capabilities}")
    tester.close_driver()
    print("[SUCCESS] WebDriver closed successfully!")
else:
    print("[FAILED] WebDriver initialization failed")
EOF
"""

        print("Running WebDriver test...")
        print("="*60)

        stdin, stdout, stderr = ssh.exec_command(test_script, timeout=60)
        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')

        if output:
            print(output)
        if error:
            print(f"Errors/Warnings:\n{error}")

        ssh.close()

        print("\n" + "="*80)
        print("Test complete!")
        print("="*80)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_webdriver()
