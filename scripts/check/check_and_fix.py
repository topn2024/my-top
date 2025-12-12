#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查并修复服务器上的 openai 库问题
"""

import paramiko
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

SERVER = "39.105.12.124"
USER = "u_topn"
PASSWORD = "TopN@2024"
DEPLOY_DIR = "/home/u_topn/TOP_N"

def execute_command(ssh, command, use_sudo=False):
    """执行 SSH 命令"""
    if use_sudo:
        command = f"echo {PASSWORD} | sudo -S {command}"

    print(f"\n执行: {command}")
    stdin, stdout, stderr = ssh.exec_command(command, timeout=120)

    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')

    if output:
        print(output)
    if error and "sudo" not in error:
        print(f"错误: {error}", file=sys.stderr)

    return output, error

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print(f"连接到服务器 {SERVER}...")
        ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=10)
        print("✓ 连接成功\n")

        print("=" * 60)
        print("检查当前 openai 版本")
        print("=" * 60)
        execute_command(ssh, f"cd {DEPLOY_DIR} && source venv/bin/activate && pip show openai")

        print("\n" + "=" * 60)
        print("卸载旧版 openai")
        print("=" * 60)
        execute_command(ssh, f"cd {DEPLOY_DIR} && source venv/bin/activate && pip uninstall openai -y")

        print("\n" + "=" * 60)
        print("安装指定版本的 openai (0.10.2)")
        print("=" * 60)
        execute_command(ssh, f"cd {DEPLOY_DIR} && source venv/bin/activate && pip install openai==0.10.2")

        print("\n" + "=" * 60)
        print("验证安装")
        print("=" * 60)
        execute_command(ssh, f"cd {DEPLOY_DIR} && source venv/bin/activate && python3 -c 'import openai; print(\"OpenAI version:\", openai.VERSION); print(\"Has ChatCompletion:\", hasattr(openai, \"ChatCompletion\"))'")

        print("\n" + "=" * 60)
        print("重启服务")
        print("=" * 60)
        execute_command(ssh, "systemctl restart topn", use_sudo=True)

        import time
        print("等待服务启动...")
        time.sleep(3)

        print("\n" + "=" * 60)
        print("检查服务状态")
        print("=" * 60)
        execute_command(ssh, "systemctl status topn --no-pager | head -15", use_sudo=True)

        print("\n" + "=" * 60)
        print("✓ 修复完成！")
        print("=" * 60)

    except Exception as e:
        print(f"✗ 错误: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
