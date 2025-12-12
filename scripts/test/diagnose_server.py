#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断服务器问题
"""

import paramiko
import sys

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"
APP_DIR = "/home/u_topn/TOP_N"

def diagnose():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)

        print("=" * 80)
        print("1. Python version")
        print("=" * 80)
        stdin, stdout, stderr = ssh.exec_command("python3 --version")
        print(stdout.read().decode())

        print("=" * 80)
        print("2. Installed packages")
        print("=" * 80)
        stdin, stdout, stderr = ssh.exec_command("pip3 list | grep -E '(flask|gunicorn|openai)'")
        print(stdout.read().decode())

        print("=" * 80)
        print("3. Test import Flask app")
        print("=" * 80)
        test_import = f"cd {APP_DIR} && python3 -c 'from backend.app import app; print(\"OK\")'"
        stdin, stdout, stderr = ssh.exec_command(test_import)
        print("STDOUT:", stdout.read().decode())
        print("STDERR:", stderr.read().decode())

        print("=" * 80)
        print("4. Try to start app manually")
        print("=" * 80)
        manual_start = f"cd {APP_DIR} && timeout 5 python3 -m flask --app backend.app run --host 0.0.0.0 --port 8081 2>&1 || true"
        stdin, stdout, stderr = ssh.exec_command(manual_start)
        print(stdout.read().decode())

        print("=" * 80)
        print("5. Check gunicorn error log")
        print("=" * 80)
        stdin, stdout, stderr = ssh.exec_command(f"cat {APP_DIR}/gunicorn_error.log 2>&1 || echo 'No log file'")
        print(stdout.read().decode())

        ssh.close()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnose()
