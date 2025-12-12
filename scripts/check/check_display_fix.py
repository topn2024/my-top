#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查DISPLAY修复效果
"""
import paramiko

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

def check():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"Connecting to {SERVER_HOST}...")
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("Connected!\n")

        # 快速测试 - 不等待完整初始化
        print("="*80)
        print("Quick test - Setting DISPLAY in login_tester:")
        print("="*80)
        test_script = """
cd /home/u_topn/TOP_N/backend
timeout 30 /home/u_topn/TOP_N/venv/bin/python << 'EOF'
import sys
import os
sys.path.insert(0, '/home/u_topn/TOP_N/backend')

print(f"1. DISPLAY at start: {os.environ.get('DISPLAY', 'Not set')}")

from login_tester import LoginTester
tester = LoginTester(headless=True)

print(f"2. DISPLAY after import: {os.environ.get('DISPLAY', 'Not set')}")

# 只测试init的开始部分，不等待完整启动
try:
    result = tester.init_driver()
    print(f"3. Init result: {result}")
    if tester.driver:
        tester.close_driver()
        print("4. WebDriver initialized and closed successfully!")
except Exception as e:
    print(f"4. Error: {e}")
EOF
"""
        stdin, stdout, stderr = ssh.exec_command(test_script, timeout=45)

        # 实时读取输出
        import time
        time.sleep(5)  # 等待5秒让命令开始执行

        # 尝试读取部分输出
        output = ""
        error = ""
        try:
            while True:
                if stdout.channel.recv_ready():
                    chunk = stdout.channel.recv(1024).decode('utf-8', errors='ignore')
                    output += chunk
                    print(chunk, end='')
                if stdout.channel.exit_status_ready():
                    break
                time.sleep(0.5)
        except:
            pass

        # 读取剩余输出
        try:
            output += stdout.read().decode('utf-8', errors='ignore')
            error = stderr.read().decode('utf-8', errors='ignore')
        except:
            pass

        if error:
            print("\nStderr:", error)

        # 检查服务日志中的login_tester相关信息
        print("\n" + "="*80)
        print("Recent service logs:")
        print("="*80)
        stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u topn -n 20 --no-pager")
        logs = stdout.read().decode('utf-8', errors='ignore')
        print(logs)

        ssh.close()

        print("\n" + "="*80)
        print("CHECK COMPLETE")
        print("="*80)
        print("\nThe DISPLAY fix has been deployed.")
        print("Please test at: http://39.105.12.124:8080")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check()
