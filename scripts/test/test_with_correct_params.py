#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import paramiko
import json
import time

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)

print("Testing with correct parameters...")
test_data = json.dumps({"company_name": "阿里巴巴", "company_desc": "阿里巴巴集团是一家中国跨国科技公司，专注于电子商务、云计算和数字媒体"})
cmd = f"""curl -X POST http://localhost:8080/api/analyze \
-H "Content-Type: application/json" \
-d '{test_data}' \
-s """

stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
response = stdout.read().decode('utf-8', errors='ignore')
print("\n=== Response ===")
print(response[:1000] if len(response) > 1000 else response)

# 检查日志看API请求路径
time.sleep(2)
stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u topn -n 5 --no-pager | grep -E '(openai|dashscope|POST)'")
logs = stdout.read().decode('utf-8', errors='ignore')
print("\n=== Recent API logs ===")
print(logs)

ssh.close()
