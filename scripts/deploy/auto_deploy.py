#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动部署脚本
将修复后的 TOP_N 应用部署到服务器
"""

import paramiko
import os
import sys
import time
import io

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 服务器配置
SERVER = "39.105.12.124"
USER = "u_topn"
PASSWORD = "TopN@2024"
DEPLOY_DIR = "/home/u_topn/TOP_N"

def print_header(text):
    """打印标题"""
    print("\n" + "=" * 50)
    print(f"  {text}")
    print("=" * 50 + "\n")

def print_step(step_num, text):
    """打印步骤"""
    print(f"\n【{step_num}】{text}")
    print("-" * 50)

def execute_command(ssh, command, use_sudo=False, timeout=30):
    """执行 SSH 命令"""
    if use_sudo:
        command = f"echo {PASSWORD} | sudo -S {command}"

    print(f"执行: {command}")
    stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)

    # 读取输出
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')

    if output:
        print(output)
    if error and "sudo" not in error:
        print(f"错误: {error}", file=sys.stderr)

    return stdout.channel.recv_exit_status()

def main():
    print_header("自动部署 TOP_N 平台到服务器 (修复版本)")

    # 创建 SSH 客户端
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # 连接到服务器
        print(f"正在连接到服务器 {SERVER}...")
        ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=10)
        print("✓ 成功连接到服务器\n")

        # 创建 SFTP 客户端用于文件传输
        sftp = ssh.open_sftp()

        # 步骤 1: 上传文件
        print_step(1, "上传修复后的文件到服务器")

        files_to_upload = [
            ("backend/app_with_upload.py", f"{DEPLOY_DIR}/backend/app_with_upload.py"),
            ("backend/app.py", f"{DEPLOY_DIR}/backend/app.py"),
            ("requirements.txt", f"{DEPLOY_DIR}/requirements.txt")
        ]

        for local_file, remote_file in files_to_upload:
            if os.path.exists(local_file):
                print(f"上传 {local_file} -> {remote_file}")
                sftp.put(local_file, remote_file)
                print(f"  ✓ {local_file} 上传成功")
            else:
                print(f"  ✗ 本地文件不存在: {local_file}")

        sftp.close()
        print("\n✓ 所有文件上传完成")

        # 步骤 2: 安装/更新依赖
        print_step(2, "安装/更新 Python 依赖")

        commands = [
            f"cd {DEPLOY_DIR}",
            "source venv/bin/activate && pip install -r requirements.txt --upgrade"
        ]

        combined_cmd = " && ".join(commands)
        execute_command(ssh, combined_cmd, timeout=120)
        print("\n✓ 依赖安装完成")

        # 步骤 3: 重启服务
        print_step(3, "重启服务")

        execute_command(ssh, "systemctl restart topn", use_sudo=True)
        print("等待服务启动...")
        time.sleep(3)
        print("✓ 服务已重启")

        # 步骤 4: 检查服务状态
        print_step(4, "检查服务状态")

        execute_command(ssh, "systemctl status topn --no-pager | head -20", use_sudo=True)

        # 步骤 5: 查看日志
        print_step(5, "查看最新日志（检查是否有错误）")

        execute_command(ssh, "journalctl -u topn -n 30 --no-pager", use_sudo=True)

        # 完成
        print_header("✓ 部署完成！")

        print("访问地址:")
        print(f"  http://{SERVER}:8080")
        print("\n管理命令:")
        print(f"  查看状态: ssh {USER}@{SERVER} 'sudo systemctl status topn'")
        print(f"  查看日志: ssh {USER}@{SERVER} 'sudo journalctl -u topn -f'")
        print(f"  重启服务: ssh {USER}@{SERVER} 'sudo systemctl restart topn'")
        print()

    except paramiko.AuthenticationException:
        print("✗ 认证失败，请检查用户名和密码", file=sys.stderr)
        sys.exit(1)
    except paramiko.SSHException as e:
        print(f"✗ SSH 连接错误: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"✗ 部署失败: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
