#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署修复后的analyze接口到服务器
"""
import paramiko
import os

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

def deploy_fixed_code():
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
        backup_cmd = "cp /home/u_topn/TOP_N/backend/app_with_upload.py /home/u_topn/TOP_N/backend/app_with_upload.py.backup_$(date +%Y%m%d_%H%M%S)"
        stdin, stdout, stderr = ssh.exec_command(backup_cmd)
        stdout.read()
        print("备份完成")

        # 上传修复后的文件
        print("\n2. 上传修复后的文件...")
        local_file = "D:\\work\\code\\TOP_N\\backend\\app_with_upload.py"
        remote_file = "/home/u_topn/TOP_N/backend/app_with_upload.py"

        sftp.put(local_file, remote_file)
        print(f"文件已上传: {local_file} -> {remote_file}")

        # 关闭SFTP
        sftp.close()

        # 重启服务
        print("\n3. 重启topn服务...")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl restart topn")
        stdout.read()
        stderr_output = stderr.read().decode('utf-8', errors='ignore')
        if stderr_output:
            print(f"重启警告: {stderr_output}")
        else:
            print("服务重启成功")

        # 等待服务启动
        import time
        print("\n4. 等待服务启动...")
        time.sleep(3)

        # 检查服务状态
        print("\n5. 检查服务状态...")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl status topn --no-pager -n 5")
        status = stdout.read().decode('utf-8', errors='ignore')
        print(status)

        # 测试analyze接口
        print("\n6. 测试analyze接口...")
        import json
        test_data = json.dumps({"company_name": "测试公司", "company_desc": "一家优秀的科技公司"})
        test_cmd = f"""curl -X POST http://localhost:8080/api/analyze \\
-H "Content-Type: application/json" \\
-d '{test_data}' \\
-s -w "\\nHTTP Code: %{{http_code}}\\n" """

        stdin, stdout, stderr = ssh.exec_command(test_cmd, timeout=120)
        response = stdout.read().decode('utf-8', errors='ignore')
        print("API响应:")
        print(response[:800] if len(response) > 800 else response)

        # 查看最新日志
        print("\n7. 查看最新服务日志...")
        stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u topn -n 15 --no-pager")
        logs = stdout.read().decode('utf-8', errors='ignore')
        print(logs)

        ssh.close()
        print("\n" + "="*80)
        print("部署完成！")
        print("="*80)

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    deploy_fixed_code()
