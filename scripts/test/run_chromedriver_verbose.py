#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
在服务器上运行ChromeDriver详细日志模式
"""
import paramiko

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

def run_verbose():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"Connecting to {SERVER_HOST}...")
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("Connected!\n")

        # 尝试直接运行chromedriver查看详细错误
        test_script = """
cd /home/u_topn/TOP_N/backend
/home/u_topn/TOP_N/venv/bin/python << 'EOF'
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os

# 设置环境变量
os.environ['DISPLAY'] = ':99'  # 虚拟显示

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--window-size=1920,1080')
chrome_options.add_argument('--verbose')
chrome_options.add_argument('--log-path=/tmp/chromedriver.log')
chrome_options.binary_location = '/usr/bin/google-chrome'

print("Trying to start WebDriver...")
try:
    driver = webdriver.Chrome(
        executable_path='/home/u_topn/chromedriver',
        options=chrome_options
    )
    print("SUCCESS: WebDriver started!")
    print(f"Title: {driver.title}")
    driver.quit()
    print("Driver closed successfully")
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()

    # 读取日志
    try:
        with open('/tmp/chromedriver.log', 'r') as f:
            print("\nChromeDriver Log:")
            print(f.read())
    except:
        pass
EOF
"""

        print("Running ChromeDriver test...")
        stdin, stdout, stderr = ssh.exec_command(test_script, timeout=60)
        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')

        if output:
            print(output)
        if error:
            print("\nStderr:", error)

        # 检查是否有依赖库缺失
        print("\n" + "="*80)
        print("Checking Chrome dependencies:")
        print("="*80)
        stdin, stdout, stderr = ssh.exec_command("ldd /usr/bin/google-chrome | grep 'not found'")
        deps = stdout.read().decode('utf-8', errors='ignore')
        if deps:
            print(f"Missing dependencies:\n{deps}")
        else:
            print("All dependencies OK")

        ssh.close()

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_verbose()
