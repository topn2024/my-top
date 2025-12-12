#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试服务器API
"""

import paramiko
import sys
import time
import json

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

def test_api():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)

        print("=" * 80)
        print("Testing Server API")
        print("=" * 80)

        # Test 1: Health check
        print("\n1. Testing /health endpoint:")
        stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8080/health")
        response = stdout.read().decode()
        print(response)

        # Test 2: Analyze API
        print("\n2. Testing /analyze endpoint:")
        test_data = json.dumps({"text": "测试公司介绍"})
        cmd = f"""curl -X POST http://localhost:8080/analyze \\
-H "Content-Type: application/json" \\
-d '{test_data}' \\
-s"""
        stdin, stdout, stderr = ssh.exec_command(cmd)
        response = stdout.read().decode()
        print(response)

        # Test 3: Check recent logs
        print("\n3. Checking recent logs:")
        stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u topn -n 20 --no-pager | tail -10")
        logs = stdout.read().decode()
        print(logs)

        ssh.close()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Waiting for server to fully start...")
    time.sleep(5)
    test_api()
