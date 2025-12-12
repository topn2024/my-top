#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署Cookie登录功能到服务器
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
        print("[OK] 文件上传成功!\n")

        # 创建Cookie目录
        print("创建Cookie目录...")
        stdin, stdout, stderr = ssh.exec_command("mkdir -p /home/u_topn/TOP_N/backend/cookies", timeout=10)
        stdout.read()
        print("[OK] Cookie目录已创建\n")

        sftp.close()

        # 重启服务
        print("重启topn服务...")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl restart topn", timeout=15)
        stdout.read()
        print("[OK] 服务已重启!\n")

        # 等待服务启动
        import time
        time.sleep(3)

        # 检查服务状态
        print("检查服务状态...")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl status topn --no-pager -n 5", timeout=10)
        status = stdout.read().decode('utf-8', errors='ignore')

        if 'active (running)' in status:
            print("[OK] 服务运行正常\n")
        else:
            print("[WARNING] 服务状态异常\n")

        print(status)

        ssh.close()

        print("\n" + "=" * 80)
        print("部署完成!")
        print("=" * 80)
        print("\nCookie登录功能已部署，特性：")
        print("  1. 首次登录成功后自动保存Cookie")
        print("  2. 后续登录自动使用Cookie，无需验证码")
        print("  3. Cookie过期时自动回退到密码登录")
        print("\n使用方法：")
        print("  1. 首次登录：手动完成验证码，系统自动保存Cookie")
        print("  2. 后续登录：系统自动使用Cookie登录，秒级完成")

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    deploy()
