#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查实际测试时的错误
"""
import paramiko
import time

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

        # 查看最新的应用日志，特别是测试账号时的日志
        print("="*80)
        print("Recent application logs (last 50 lines):")
        print("="*80)
        stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u topn -n 50 --no-pager")
        logs = stdout.read().decode('utf-8', errors='ignore')
        print(logs)

        # 检查账号数据文件
        print("\n" + "="*80)
        print("Checking accounts.json:")
        print("="*80)
        stdin, stdout, stderr = ssh.exec_command("cat /home/u_topn/TOP_N/backend/accounts.json 2>/dev/null || echo 'File not found'")
        accounts = stdout.read().decode('utf-8', errors='ignore')
        print(accounts)

        # 模拟Flask应用调用test_account_login
        print("\n" + "="*80)
        print("Simulating Flask app calling test_account_login:")
        print("="*80)
        test_script = """
cd /home/u_topn/TOP_N/backend
/home/u_topn/TOP_N/venv/bin/python << 'EOF'
import sys
import os
sys.path.insert(0, '/home/u_topn/TOP_N/backend')

print(f"Initial DISPLAY: {os.environ.get('DISPLAY', 'Not set')}")

# 模拟Flask应用的导入和调用
try:
    from login_tester import test_account_login
    print("Successfully imported test_account_login")

    # 测试知乎登录（使用假账号）
    result = test_account_login('知乎', 'test_user', 'test_pass', headless=True)
    print(f"\nTest result: {result}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print(f"\nFinal DISPLAY: {os.environ.get('DISPLAY', 'Not set')}")
EOF
"""
        stdin, stdout, stderr = ssh.exec_command(test_script, timeout=120)

        # 等待一段时间让命令执行
        time.sleep(10)

        output = ""
        error = ""
        try:
            # 尝试实时读取
            while not stdout.channel.exit_status_ready():
                if stdout.channel.recv_ready():
                    chunk = stdout.channel.recv(1024).decode('utf-8', errors='ignore')
                    output += chunk
                    print(chunk, end='')
                time.sleep(0.5)

            # 读取剩余输出
            remaining = stdout.read().decode('utf-8', errors='ignore')
            output += remaining
            print(remaining, end='')

            error = stderr.read().decode('utf-8', errors='ignore')
        except Exception as e:
            print(f"\nRead error: {e}")

        if error:
            print("\nStderr:", error)

        # 再次查看日志，看是否有新的错误
        print("\n" + "="*80)
        print("Latest logs after test:")
        print("="*80)
        stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u topn -n 30 --no-pager | tail -20")
        logs = stdout.read().decode('utf-8', errors='ignore')
        print(logs)

        ssh.close()

        print("\n" + "="*80)
        print("CHECK COMPLETE")
        print("="*80)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check()
