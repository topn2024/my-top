#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署账号配置功能到服务器
"""
import paramiko
import os

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

def deploy():
    try:
        # 连接服务器
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"正在连接服务器 {SERVER_HOST}...")
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("服务器连接成功！")

        # 创建SFTP客户端
        sftp = ssh.open_sftp()

        # 备份现有文件
        print("\n1. 备份现有文件...")
        backup_cmd = "cp /home/u_topn/TOP_N/backend/app_with_upload.py /home/u_topn/TOP_N/backend/app_with_upload.py.backup_accounts_$(date +%Y%m%d_%H%M%S)"
        stdin, stdout, stderr = ssh.exec_command(backup_cmd)
        stdout.read()
        print("后端文件备份完成")

        # 上传文件
        print("\n2. 上传更新的文件...")

        files_to_upload = [
            ("D:\\work\\code\\TOP_N\\backend\\app_with_upload.py", "/home/u_topn/TOP_N/backend/app_with_upload.py"),
            ("D:\\work\\code\\TOP_N\\templates\\index.html", "/home/u_topn/TOP_N/templates/index.html"),
            ("D:\\work\\code\\TOP_N\\static\\style.css", "/home/u_topn/TOP_N/static/style.css"),
            ("D:\\work\\code\\TOP_N\\static\\account_config.js", "/home/u_topn/TOP_N/static/account_config.js"),
        ]

        for local_file, remote_file in files_to_upload:
            print(f"  上传: {os.path.basename(local_file)}")
            sftp.put(local_file, remote_file)

        print("所有文件上传完成")

        # 创建accounts目录
        print("\n3. 创建accounts目录...")
        stdin, stdout, stderr = ssh.exec_command("mkdir -p /home/u_topn/TOP_N/accounts")
        stdout.read()
        print("目录创建完成")

        # 关闭SFTP
        sftp.close()

        # 重启服务
        print("\n4. 重启topn服务...")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl restart topn")
        stdout.read()
        stderr_output = stderr.read().decode('utf-8', errors='ignore')
        if stderr_output:
            print(f"重启警告: {stderr_output}")
        else:
            print("服务重启成功")

        # 等待服务启动
        import time
        print("\n5. 等待服务启动...")
        time.sleep(3)

        # 检查服务状态
        print("\n6. 检查服务状态...")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl status topn --no-pager -n 5")
        status = stdout.read().decode('utf-8', errors='ignore')
        print(status)

        # 测试账号API
        print("\n7. 测试账号API...")
        import json

        # 测试GET接口
        test_cmd = """curl -s -X GET http://localhost:8080/api/accounts"""
        stdin, stdout, stderr = ssh.exec_command(test_cmd, timeout=30)
        response = stdout.read().decode('utf-8', errors='ignore')
        print("GET /api/accounts 响应:")
        print(response[:500] if len(response) > 500 else response)

        # 测试POST接口 - 添加一个测试账号
        test_data = json.dumps({
            "platform": "知乎",
            "username": "test_account",
            "password": "test_pass",
            "notes": "部署测试账号"
        })
        test_cmd = f"""curl -s -X POST http://localhost:8080/api/accounts \\
-H "Content-Type: application/json" \\
-d '{test_data}'"""

        print("\nPOST /api/accounts 测试:")
        stdin, stdout, stderr = ssh.exec_command(test_cmd, timeout=30)
        response = stdout.read().decode('utf-8', errors='ignore')
        print(response)

        # 再次获取账号列表
        print("\n再次获取账号列表:")
        stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8080/api/accounts", timeout=30)
        response = stdout.read().decode('utf-8', errors='ignore')
        print(response[:500] if len(response) > 500 else response)

        # 查看最新日志
        print("\n8. 查看最新服务日志...")
        stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u topn -n 20 --no-pager | tail -15")
        logs = stdout.read().decode('utf-8', errors='ignore')
        print(logs)

        ssh.close()
        print("\n" + "="*80)
        print("部署完成！")
        print("="*80)
        print("\n访问 http://39.105.12.124:8080 测试账号配置功能")
        print("点击右上角的【⚙️ 账号配置】按钮即可使用")

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    deploy()
