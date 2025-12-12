#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import paramiko, sys, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER = "39.105.12.124"
USER = "u_topn"
PASSWORD = "TopN@2024"

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=10)
    print(f"✓ 连接成功: {USER}@{SERVER}\n")

    print("查看start.sh内容:")
    stdin, stdout, stderr = ssh.exec_command("cat /home/u_topn/TOP_N/start.sh")
    print(stdout.read().decode())

    print("\n\n检查端口占用:")
    stdin, stdout, stderr = ssh.exec_command("netstat -tuln | grep -E ':(3001|8080)'")
    print(stdout.read().decode())

    ssh.close()
except Exception as e:
    print(f"错误: {e}")
