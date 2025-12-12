#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
在服务器上测试Chrome执行
"""
import paramiko

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

def test_chrome():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"Connecting to {SERVER_HOST}...")
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("Connected!\n")

        # 1. 测试Chrome版本命令
        print("="*80)
        print("1. Testing: google-chrome --version")
        print("="*80)
        stdin, stdout, stderr = ssh.exec_command("google-chrome --version")
        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')
        print(f"Output: {output}")
        if error:
            print(f"Error: {error}")

        # 2. 测试Chrome headless模式
        print("\n" + "="*80)
        print("2. Testing: google-chrome --headless --disable-gpu --dump-dom")
        print("="*80)
        test_cmd = "timeout 5 google-chrome --headless --disable-gpu --no-sandbox --dump-dom https://www.baidu.com 2>&1 | head -20"
        stdin, stdout, stderr = ssh.exec_command(test_cmd, timeout=10)
        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')

        if output:
            print(f"Output (first 500 chars):\n{output[:500]}")
        if error:
            print(f"Error: {error[:500]}")

        # 3. 使用DISPLAY=:99测试
        print("\n" + "="*80)
        print("3. Testing: DISPLAY=:99 google-chrome --headless")
        print("="*80)
        test_cmd = "DISPLAY=:99 timeout 5 google-chrome --headless --disable-gpu --no-sandbox --dump-dom https://www.baidu.com 2>&1 | head -20"
        stdin, stdout, stderr = ssh.exec_command(test_cmd, timeout=10)
        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')

        if output:
            print(f"Output (first 500 chars):\n{output[:500]}")
        if error:
            print(f"Error: {error[:500]}")

        # 4. 测试作为u_topn用户执行
        print("\n" + "="*80)
        print("4. Testing: As user u_topn with DISPLAY=:99")
        print("="*80)
        test_cmd = "sudo -u u_topn DISPLAY=:99 HOME=/home/u_topn timeout 5 google-chrome --headless --disable-gpu --no-sandbox --dump-dom https://www.baidu.com 2>&1 | head -20"
        stdin, stdout, stderr = ssh.exec_command(test_cmd, timeout=10)
        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')

        if output:
            print(f"Output (first 500 chars):\n{output[:500]}")
        if error:
            print(f"Error: {error[:500]}")

        # 5. 完整的WebDriver测试
        print("\n" + "="*80)
        print("5. Full WebDriver test:")
        print("="*80)
        test_script = """
cd /home/u_topn/TOP_N/backend
DISPLAY=:99 timeout 30 /home/u_topn/TOP_N/venv/bin/python << 'EOF'
import sys
import os
sys.path.insert(0, '/home/u_topn/TOP_N/backend')

os.environ['DISPLAY'] = ':99'

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

print("Setting up Chrome options...")
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
chrome_options.binary_location = '/usr/bin/google-chrome'

print("Initializing WebDriver...")
try:
    driver = webdriver.Chrome(
        executable_path='/home/u_topn/chromedriver',
        options=chrome_options
    )
    print("SUCCESS: WebDriver initialized!")
    print(f"Navigating to baidu.com...")
    driver.get('https://www.baidu.com')
    print(f"Page title: {driver.title}")
    driver.quit()
    print("WebDriver closed successfully")
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
EOF
"""
        stdin, stdout, stderr = ssh.exec_command(test_script, timeout=45)

        import time
        time.sleep(5)

        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')

        if output:
            print(output)
        if error and 'WDM' not in error:
            print(f"Stderr: {error[:1000]}")

        ssh.close()

        print("\n" + "="*80)
        print("TEST COMPLETE")
        print("="*80)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chrome()
