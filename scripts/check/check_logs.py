#!/usr/bin/env python3
import sys, subprocess
try: import paramiko
except: subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "paramiko"]); import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("39.105.12.124", 22, "u_topn", "TopN@2024", timeout=30)

# 检查配置日志
print("="*60)
print("配置日志(最后20行):")
print("="*60)
stdin, stdout, stderr = ssh.exec_command("tail -20 /tmp/config.log 2>&1")
print(stdout.read().decode('utf-8', errors='ignore'))

# 检查编译日志
print("\n" + "="*60)
print("编译日志(最后30行):")
print("="*60)
stdin, stdout, stderr = ssh.exec_command("tail -30 /tmp/make.log 2>&1")
print(stdout.read().decode('utf-8', errors='ignore'))

# 检查源码目录
print("\n" + "="*60)
print("源码目录状态:")
print("="*60)
stdin, stdout, stderr = ssh.exec_command("ls -lh /tmp/Python-3.13.1 2>&1 | head -20")
print(stdout.read().decode('utf-8', errors='ignore'))

# 检查make进程
print("\n" + "="*60)
print("make进程状态:")
print("="*60)
stdin, stdout, stderr = ssh.exec_command("ps aux | grep make | grep -v grep")
print(stdout.read().decode('utf-8', errors='ignore') or "没有make进程在运行")

ssh.close()
