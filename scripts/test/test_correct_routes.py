#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import paramiko
import json

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)

print("=" * 80)
print("Testing CORRECT API routes")
print("=" * 80)

# Test 1: /api/health
print("\n1. Testing /api/health:")
stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8080/api/health")
print(stdout.read().decode())

# Test 2: /api/analyze
print("\n2. Testing /api/analyze:")
test_data = json.dumps({"text": "测试公司：一家优秀的科技公司"})
cmd = f"""curl -X POST http://localhost:8080/api/analyze \\
-H "Content-Type: application/json" \\
-d '{test_data}' \\
-s"""
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
response = stdout.read().decode()
print(response[:500] if len(response) > 500 else response)  # 打印前500字符

ssh.close()
