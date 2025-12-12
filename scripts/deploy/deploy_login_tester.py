#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署优化后的login_tester.py到服务器
"""
import paramiko

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

def deploy():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"连接到服务器 {SERVER_HOST}...")
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("连接成功!\n")

        # 上传文件
        sftp = ssh.open_sftp()
        local_file = "D:/work/code/TOP_N/backend/login_tester.py"
        remote_file = "/home/u_topn/TOP_N/backend/login_tester.py"

        print(f"上传文件...")
        print(f"  本地: {local_file}")
        print(f"  远程: {remote_file}")

        sftp.put(local_file, remote_file)
        print("✓ 文件上传成功!\n")

        sftp.close()

        # 重启服务
        print("重启topn服务...")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl restart topn", timeout=10)
        stdout.read()  # 等待命令执行
        print("✓ 服务已重启!\n")

        # 检查服务状态
        print("检查服务状态...")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl status topn --no-pager -n 3", timeout=10)
        status = stdout.read().decode('utf-8', errors='ignore')
        print(status)

        ssh.close()

        print("\n" + "=" * 80)
        print("部署完成!")
        print("=" * 80)

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    deploy()
