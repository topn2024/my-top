#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断Chrome运行环境问题
检查systemd环境、依赖库、xvfb等
"""
import paramiko
import time

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

def diagnose():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"Connecting to {SERVER_HOST}...")
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("Connected!\n")

        # 1. 检查Chrome依赖库
        print("="*80)
        print("1. Checking Chrome shared library dependencies:")
        print("="*80)
        stdin, stdout, stderr = ssh.exec_command("ldd /usr/bin/google-chrome | grep 'not found'")
        deps = stdout.read().decode('utf-8', errors='ignore')
        if deps:
            print(f"[X] Missing dependencies:\n{deps}")
        else:
            print("[OK] All Chrome dependencies are satisfied")

        # 2. 检查systemd服务环境变量
        print("\n" + "="*80)
        print("2. Checking systemd service environment:")
        print("="*80)
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl show topn --property=Environment")
        env = stdout.read().decode('utf-8', errors='ignore')
        print(f"Service environment:\n{env}")

        # 3. 检查是否安装了xvfb
        print("\n" + "="*80)
        print("3. Checking xvfb (virtual framebuffer):")
        print("="*80)
        stdin, stdout, stderr = ssh.exec_command("which xvfb-run")
        xvfb_path = stdout.read().decode('utf-8', errors='ignore').strip()
        if xvfb_path:
            print(f"[OK] xvfb-run found at: {xvfb_path}")
        else:
            print("[X] xvfb-run not found - installing...")
            stdin, stdout, stderr = ssh.exec_command("sudo apt-get install -y xvfb")
            install_output = stdout.read().decode('utf-8', errors='ignore')
            print(install_output[:500])

        # 4. 测试使用xvfb-run启动Chrome
        print("\n" + "="*80)
        print("4. Testing Chrome with xvfb-run:")
        print("="*80)
        test_script = """
cd /home/u_topn/TOP_N/backend
/home/u_topn/TOP_N/venv/bin/python << 'EOF'
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os

# 设置DISPLAY环境变量
os.environ['DISPLAY'] = ':99'

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--window-size=1920,1080')
chrome_options.binary_location = '/usr/bin/google-chrome'

try:
    driver = webdriver.Chrome(
        executable_path='/home/u_topn/chromedriver',
        options=chrome_options
    )
    print("[OK] SUCCESS: WebDriver started with DISPLAY=:99")
    print(f"Title: {driver.title}")
    driver.quit()
except Exception as e:
    print(f"[X] FAILED: {e}")
    import traceback
    traceback.print_exc()
EOF
"""
        stdin, stdout, stderr = ssh.exec_command(f"xvfb-run -a {test_script}", timeout=60)
        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')

        if output:
            print(output)
        if error:
            print("Stderr:", error)

        # 5. 检查Chrome crash日志
        print("\n" + "="*80)
        print("5. Checking Chrome crash logs:")
        print("="*80)
        stdin, stdout, stderr = ssh.exec_command("ls -lh /tmp/chrome* /tmp/.org.chromium* 2>/dev/null | head -20")
        crash_files = stdout.read().decode('utf-8', errors='ignore')
        if crash_files:
            print(crash_files)
        else:
            print("No crash files found in /tmp")

        # 6. 测试在systemd服务用户环境下运行
        print("\n" + "="*80)
        print("6. Testing as systemd service user (u_topn):")
        print("="*80)
        stdin, stdout, stderr = ssh.exec_command("sudo -u u_topn HOME=/home/u_topn DISPLAY=:99 /home/u_topn/TOP_N/venv/bin/python -c 'from selenium import webdriver; from selenium.webdriver.chrome.options import Options; opts = Options(); opts.add_argument(\"--headless\"); opts.add_argument(\"--no-sandbox\"); opts.add_argument(\"--disable-dev-shm-usage\"); opts.binary_location=\"/usr/bin/google-chrome\"; driver = webdriver.Chrome(executable_path=\"/home/u_topn/chromedriver\", options=opts); print(\"SUCCESS\"); driver.quit()'")
        result = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')

        print("Output:", result)
        if error:
            print("Error:", error)

        # 7. 检查Chrome进程权限
        print("\n" + "="*80)
        print("7. Checking Chrome binary permissions:")
        print("="*80)
        stdin, stdout, stderr = ssh.exec_command("ls -l /usr/bin/google-chrome")
        perms = stdout.read().decode('utf-8', errors='ignore')
        print(perms)

        # 8. 检查/tmp目录权限
        print("\n" + "="*80)
        print("8. Checking /tmp directory permissions:")
        print("="*80)
        stdin, stdout, stderr = ssh.exec_command("ls -ld /tmp /dev/shm")
        tmp_perms = stdout.read().decode('utf-8', errors='ignore')
        print(tmp_perms)

        ssh.close()

        print("\n" + "="*80)
        print("DIAGNOSIS COMPLETE")
        print("="*80)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnose()
