#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时监控服务器日志
"""
import paramiko
import sys
import time

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

def monitor_logs():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)

        print("=" * 80)
        print("Monitoring Server Logs - Press Ctrl+C to stop")
        print("=" * 80)
        print("\n1. Recent logs (last 50 lines):")
        print("-" * 80)

        # 显示最近的日志
        stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u topn -n 50 --no-pager")
        recent_logs = stdout.read().decode('utf-8', errors='ignore')
        print(recent_logs)

        print("\n2. Checking Flask app routes:")
        print("-" * 80)
        stdin, stdout, stderr = ssh.exec_command("cd /home/u_topn/TOP_N/backend && grep -n '@app.route' app.py")
        routes = stdout.read().decode('utf-8', errors='ignore')
        print(routes)

        print("\n3. Testing file upload endpoint:")
        print("-" * 80)

        # 测试文件上传相关的端点
        test_commands = [
            ("GET /", "curl -s http://localhost:8080/ | head -20"),
            ("POST /api/analyze (without company)", "curl -X POST http://localhost:8080/api/analyze -H 'Content-Type: application/json' -d '{}' -s"),
            ("Check if upload route exists", "cd /home/u_topn/TOP_N/backend && grep -A 5 'upload' app.py | head -20"),
        ]

        for desc, cmd in test_commands:
            print(f"\n{desc}:")
            stdin, stdout, stderr = ssh.exec_command(cmd)
            result = stdout.read().decode('utf-8', errors='ignore')
            print(result[:300] if len(result) > 300 else result)

        print("\n4. Live monitoring (last 10 seconds of logs):")
        print("-" * 80)
        print("Waiting for new requests...")

        # 开始实时监控
        transport = ssh.get_transport()
        channel = transport.open_session()
        channel.exec_command("sudo journalctl -u topn -f")

        start_time = time.time()
        while time.time() - start_time < 30:  # 监控30秒
            if channel.recv_ready():
                output = channel.recv(4096).decode('utf-8', errors='ignore')
                print(output, end='')
            time.sleep(0.5)

        channel.close()
        ssh.close()

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    monitor_logs()
