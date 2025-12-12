#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查分析接口错误
"""
import paramiko
import sys
import time
import json

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

def check_analyze_error():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)

        print("=" * 80)
        print("Checking Analyze API Error")
        print("=" * 80)

        # 1. 查看最近的日志（特别是404错误）
        print("\n1. Recent logs with 404 errors:")
        print("-" * 80)
        stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u topn -n 100 --no-pager | grep -E '(404|POST|GET)' | tail -30")
        logs = stdout.read().decode('utf-8', errors='ignore')
        print(logs)

        # 2. 检查app_with_upload.py的所有路由
        print("\n2. All routes in app_with_upload.py:")
        print("-" * 80)
        stdin, stdout, stderr = ssh.exec_command("grep -n '@app.route' /home/u_topn/TOP_N/backend/app_with_upload.py")
        routes = stdout.read().decode('utf-8', errors='ignore')
        print(routes)

        # 3. 查看前端JavaScript调用的API
        print("\n3. Check frontend API calls:")
        print("-" * 80)
        stdin, stdout, stderr = ssh.exec_command("grep -n 'fetch\\|/api/' /home/u_topn/TOP_N/static/app_upload.js | head -20")
        api_calls = stdout.read().decode('utf-8', errors='ignore')
        print(api_calls)

        # 4. 测试analyze接口（使用正确的参数）
        print("\n4. Testing /api/analyze with company name:")
        print("-" * 80)
        test_data = json.dumps({"company": "测试公司", "text": "一家优秀的科技公司"})
        cmd = f"""curl -X POST http://localhost:8080/api/analyze \\
-H "Content-Type: application/json" \\
-d '{test_data}' \\
-s -w "\\nHTTP Code: %{{http_code}}\\n" """
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
        response = stdout.read().decode('utf-8', errors='ignore')
        print(response[:500] if len(response) > 500 else response)

        # 5. 检查是否有其他analyze相关的路由
        print("\n5. Checking for analyze-related routes:")
        print("-" * 80)
        stdin, stdout, stderr = ssh.exec_command("grep -i 'analyze' /home/u_topn/TOP_N/backend/app_with_upload.py | grep -n 'def\\|@app.route'")
        analyze_routes = stdout.read().decode('utf-8', errors='ignore')
        print(analyze_routes)

        # 6. 实时监控接下来的请求
        print("\n6. Real-time monitoring (waiting 20 seconds for requests):")
        print("-" * 80)
        print("Please trigger the analyze button in the frontend now...")

        transport = ssh.get_transport()
        channel = transport.open_session()
        channel.exec_command("sudo journalctl -u topn -f")

        start_time = time.time()
        while time.time() - start_time < 20:
            if channel.recv_ready():
                output = channel.recv(4096).decode('utf-8', errors='ignore')
                if '404' in output or 'POST' in output or 'GET' in output:
                    print(output, end='')
            time.sleep(0.5)

        channel.close()
        ssh.close()

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_analyze_error()
