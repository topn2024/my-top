#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的analyze接口
"""
import paramiko
import json
import time

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)

print("=" * 80)
print("Testing Fixed Analyze API")
print("=" * 80)

# 等待服务完全启动
print("\nWaiting for service to fully start...")
time.sleep(3)

# 测试analyze接口
print("\n1. Testing /api/analyze with proper data:")
print("-" * 80)
test_data = json.dumps({"company": "阿里巴巴", "text": "阿里巴巴集团是一家中国跨国科技公司"})
cmd = f"""curl -X POST http://localhost:8080/api/analyze \\
-H "Content-Type: application/json" \\
-d '{test_data}' \\
-s -w "\\nHTTP Code: %{{http_code}}\\n" """

stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
response = stdout.read().decode('utf-8', errors='ignore')
print(response[:800] if len(response) > 800 else response)

# 检查日志
print("\n2. Checking recent logs:")
print("-" * 80)
stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u topn -n 20 --no-pager | tail -10")
logs = stdout.read().decode('utf-8', errors='ignore')
print(logs)

ssh.close()
print("\n" + "=" * 80)
print("Test completed!")
print("=" * 80)
