#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import paramiko

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)

print("=" * 80)
print("1. Check systemd service file")
print("=" * 80)
stdin, stdout, stderr = ssh.exec_command("cat /etc/systemd/system/topn.service")
print(stdout.read().decode())

print("\n" + "=" * 80)
print("2. Check what app.py exists in /home/u_topn/TOP_N/")
print("=" * 80)
stdin, stdout, stderr = ssh.exec_command("ls -la /home/u_topn/TOP_N/ | grep app.py")
print(stdout.read().decode())

print("\n" + "=" * 80)
print("3. Check if app.py has correct content")
print("=" * 80)
stdin, stdout, stderr = ssh.exec_command("head -20 /home/u_topn/TOP_N/app.py 2>&1 || echo 'File not found'")
print(stdout.read().decode())

print("\n" + "=" * 80)
print("4. Check backend/app.py routes")
print("=" * 80)
stdin, stdout, stderr = ssh.exec_command("grep -n '@app.route' /home/u_topn/TOP_N/backend/app.py")
print(stdout.read().decode())

ssh.close()
