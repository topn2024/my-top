#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查服务器Chrome和ChromeDriver安装情况
"""
import paramiko

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

def check_chrome():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"Connecting to {SERVER_HOST}...")
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("Connected!\n")

        # 1. 检查Chrome是否安装
        print("="*80)
        print("1. Checking Chrome installation:")
        print("="*80)
        stdin, stdout, stderr = ssh.exec_command("which google-chrome")
        chrome_path = stdout.read().decode('utf-8', errors='ignore').strip()
        if chrome_path:
            print(f"[OK] Chrome found at: {chrome_path}")

            # 检查Chrome版本
            stdin, stdout, stderr = ssh.exec_command("google-chrome --version")
            chrome_version = stdout.read().decode('utf-8', errors='ignore').strip()
            print(f"[OK] Chrome version: {chrome_version}")
        else:
            print("[X] Chrome not found")

        # 2. 检查ChromeDriver是否安装
        print("\n" + "="*80)
        print("2. Checking ChromeDriver installation:")
        print("="*80)

        # 检查多个可能的位置
        chromedriver_locations = [
            '/home/u_topn/chromedriver',
            '/usr/local/bin/chromedriver',
            '/usr/bin/chromedriver',
        ]

        found_chromedriver = False
        for location in chromedriver_locations:
            stdin, stdout, stderr = ssh.exec_command(f"test -f {location} && echo 'exists' || echo 'not found'")
            result = stdout.read().decode('utf-8', errors='ignore').strip()
            if result == 'exists':
                print(f"[OK] ChromeDriver found at: {location}")

                # 检查版本
                stdin, stdout, stderr = ssh.exec_command(f"{location} --version")
                version = stdout.read().decode('utf-8', errors='ignore').strip()
                print(f"[OK] ChromeDriver version: {version}")

                # 检查执行权限
                stdin, stdout, stderr = ssh.exec_command(f"ls -l {location}")
                perms = stdout.read().decode('utf-8', errors='ignore').strip()
                print(f"[OK] Permissions: {perms}")

                found_chromedriver = True
                break

        if not found_chromedriver:
            print("[X] ChromeDriver not found in common locations")

        # 3. 检查Xvfb状态
        print("\n" + "="*80)
        print("3. Checking Xvfb (Virtual Display):")
        print("="*80)
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl status xvfb --no-pager -n 3")
        xvfb_status = stdout.read().decode('utf-8', errors='ignore')
        if 'active (running)' in xvfb_status.lower():
            print("[OK] Xvfb is running")
        else:
            print("[X] Xvfb is not running")
        print(xvfb_status)

        # 4. 检查Xvfb进程
        print("\n" + "="*80)
        print("4. Checking Xvfb process:")
        print("="*80)
        stdin, stdout, stderr = ssh.exec_command("ps aux | grep Xvfb | grep -v grep")
        xvfb_proc = stdout.read().decode('utf-8', errors='ignore').strip()
        if xvfb_proc:
            print(f"[OK] Xvfb process:\n{xvfb_proc}")
        else:
            print("[X] No Xvfb process found")

        # 5. 检查topn服务环境变量
        print("\n" + "="*80)
        print("5. Checking topn service environment:")
        print("="*80)
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl show topn --property=Environment")
        env = stdout.read().decode('utf-8', errors='ignore').strip()
        print(f"Service environment: {env}")

        if 'DISPLAY=:99' in env:
            print("[OK] DISPLAY environment variable is set")
        else:
            print("[X] DISPLAY environment variable is NOT set")

        # 6. 测试WebDriver初始化
        print("\n" + "="*80)
        print("6. Testing WebDriver initialization:")
        print("="*80)
        test_script = """
cd /home/u_topn/TOP_N/backend
timeout 30 /home/u_topn/TOP_N/venv/bin/python << 'EOF'
import sys
import os
sys.path.insert(0, '/home/u_topn/TOP_N/backend')

print(f"DISPLAY: {os.environ.get('DISPLAY', 'Not set')}")

try:
    from login_tester import LoginTester
    tester = LoginTester(headless=True)
    result = tester.init_driver()

    if result:
        print("[OK] WebDriver initialized successfully!")
        tester.close_driver()
    else:
        print("[X] WebDriver initialization failed")
except Exception as e:
    print(f"[X] Error: {e}")
    import traceback
    traceback.print_exc()
EOF
"""
        stdin, stdout, stderr = ssh.exec_command(test_script, timeout=45)

        import time
        time.sleep(3)

        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')

        if output:
            print(output)
        if error and 'WDM' not in error:
            print("Stderr:", error)

        # 7. 检查Chrome依赖库
        print("\n" + "="*80)
        print("7. Checking Chrome dependencies:")
        print("="*80)
        stdin, stdout, stderr = ssh.exec_command("ldd /usr/bin/google-chrome | grep 'not found'")
        missing_deps = stdout.read().decode('utf-8', errors='ignore').strip()
        if missing_deps:
            print(f"[X] Missing dependencies:\n{missing_deps}")
        else:
            print("[OK] All dependencies are satisfied")

        ssh.close()

        print("\n" + "="*80)
        print("CHECK COMPLETE")
        print("="*80)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_chrome()
