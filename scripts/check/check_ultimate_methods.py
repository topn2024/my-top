#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 LoginTesterUltimate 的方法
"""
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)

        # 检查方法名
        cmd = "cd /home/u_topn/TOP_N/backend && grep 'def ' login_tester_ultimate.py | grep -v '__' | head -15"
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        output = stdout.read().decode('utf-8')
        print("LoginTesterUltimate 的方法:")
        print(output)

        ssh.close()

    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    main()
