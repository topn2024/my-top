#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import paramiko
import sys
import io
import time

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

SERVER = "39.105.12.124"
USER = "u_topn"
PASSWORD = "TopN@2024"
DEPLOY_DIR = "/home/u_topn/TOP_N"

def execute(ssh, cmd, timeout=120):
    print(f"\n$ {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    if out:
        print(out)
    if err and 'sudo' not in err and 'WARNING' not in err:
        print("ERR:", err)
    return out

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=10)

print("=" * 60)
print("安装 openai 0.8.0 和更新 requirements.txt")
print("=" * 60)
execute(ssh, f"cd {DEPLOY_DIR} && source venv/bin/activate && pip install openai==0.8.0")

print("\n" + "=" * 60)
print("验证安装")
print("=" * 60)
execute(ssh, f"cd {DEPLOY_DIR} && source venv/bin/activate && pip show openai")
execute(ssh, f"cd {DEPLOY_DIR}/backend && {DEPLOY_DIR}/venv/bin/python3 -c 'import openai; print(\"OK, version:\", openai.VERSION)'")

print("\n" + "=" * 60)
print("重启服务")
print("=" * 60)
execute(ssh, f"echo {PASSWORD} | sudo -S systemctl restart topn")
time.sleep(3)

print("\n" + "=" * 60)
print("检查服务状态")
print("=" * 60)
execute(ssh, f"echo {PASSWORD} | sudo -S systemctl status topn --no-pager | head -20")

ssh.close()
print("\n✓ 完成！")
