#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置SSH免密登录
"""
import paramiko
import os
import sys
import io

# 设置标准输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

# 读取本地公钥
home_dir = os.path.expanduser("~")
pub_key_path = os.path.join(home_dir, ".ssh", "id_rsa.pub")

with open(pub_key_path, 'r') as f:
    pub_key = f.read().strip()

print(f"✓ 读取到公钥: {pub_key[:50]}...")

try:
    # 连接服务器
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
    print(f"✓ 已连接到服务器 {SERVER_HOST}")

    # 创建.ssh目录（如果不存在）
    commands = [
        "mkdir -p ~/.ssh",
        "chmod 700 ~/.ssh",
        "touch ~/.ssh/authorized_keys",
        "chmod 600 ~/.ssh/authorized_keys"
    ]

    for cmd in commands:
        stdin, stdout, stderr = ssh.exec_command(cmd)
        stdout.read()  # 等待命令完成

    print("✓ 已创建.ssh目录和authorized_keys文件")

    # 检查公钥是否已经存在
    stdin, stdout, stderr = ssh.exec_command(f"grep '{pub_key}' ~/.ssh/authorized_keys")
    existing = stdout.read().decode('utf-8')

    if existing.strip():
        print("✓ 公钥已存在于authorized_keys中")
    else:
        # 添加公钥到authorized_keys
        stdin, stdout, stderr = ssh.exec_command(f"echo '{pub_key}' >> ~/.ssh/authorized_keys")
        stdout.read()
        print("✓ 公钥已添加到authorized_keys")

    # 验证文件权限
    stdin, stdout, stderr = ssh.exec_command("ls -la ~/.ssh/authorized_keys")
    permissions = stdout.read().decode('utf-8')
    print(f"✓ authorized_keys权限: {permissions.strip()}")

    ssh.close()

    print("\n" + "=" * 60)
    print("✅ SSH免密登录配置完成!")
    print("=" * 60)
    print("\n现在可以测试免密登录:")
    print(f"  ssh {SERVER_USER}@{SERVER_HOST}")
    print("\n如果仍需要密码，请检查:")
    print("  1. 服务器的/etc/ssh/sshd_config中PubkeyAuthentication是否为yes")
    print("  2. 服务器的~/.ssh目录权限是否为700")
    print("  3. 服务器的~/.ssh/authorized_keys权限是否为600")

except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
