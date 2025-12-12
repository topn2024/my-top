#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署账号配置功能V2 - 包含平台选择和登录测试
"""
import paramiko
import os

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

def deploy():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"正在连接服务器 {SERVER_HOST}...")
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("服务器连接成功！")

        sftp = ssh.open_sftp()

        # 备份
        print("\n1. 备份现有文件...")
        backup_cmd = "cp /home/u_topn/TOP_N/backend/app_with_upload.py /home/u_topn/TOP_N/backend/app_with_upload.py.backup_v2_$(date +%Y%m%d_%H%M%S)"
        stdin, stdout, stderr = ssh.exec_command(backup_cmd)
        stdout.read()
        print("备份完成")

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
        sftp.close()

        # 重启服务
        print("\n3. 重启topn服务...")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl restart topn")
        stdout.read()
        print("服务重启成功")

        import time
        print("\n4. 等待服务启动...")
        time.sleep(3)

        # 检查服务状态
        print("\n5. 检查服务状态...")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl status topn --no-pager -n 5")
        status = stdout.read().decode('utf-8', errors='ignore')
        print(status)

        # 测试新功能
        print("\n6. 测试新功能...")

        import json

        # 测试添加账号（使用下拉平台）
        test_data = json.dumps({
            "platform": "知乎",
            "username": "test_zhihu",
            "password": "test123",
            "notes": "测试账号-知乎"
        })
        test_cmd = f"""curl -s -X POST http://localhost:8080/api/accounts \\
-H "Content-Type: application/json" \\
-d '{test_data}'"""

        print("\n添加测试账号:")
        stdin, stdout, stderr = ssh.exec_command(test_cmd, timeout=30)
        response = stdout.read().decode('utf-8', errors='ignore')
        print(response)

        # 解析响应获取账号ID
        try:
            result = json.loads(response)
            if result.get('success'):
                account_id = result['account']['id']
                print(f"\n账号添加成功，ID: {account_id}")

                # 测试登录功能
                print("\n测试登录验证:")
                test_cmd = f"curl -s -X POST http://localhost:8080/api/accounts/{account_id}/test"
                stdin, stdout, stderr = ssh.exec_command(test_cmd, timeout=30)
                test_response = stdout.read().decode('utf-8', errors='ignore')
                print(test_response)

                # 再次获取账号列表查看状态
                print("\n查看账号状态:")
                stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8080/api/accounts", timeout=30)
                accounts_response = stdout.read().decode('utf-8', errors='ignore')
                print(accounts_response[:800] if len(accounts_response) > 800 else accounts_response)
        except:
            print("无法解析响应")

        # 查看日志
        print("\n7. 查看最新日志...")
        stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u topn -n 20 --no-pager | tail -15")
        logs = stdout.read().decode('utf-8', errors='ignore')
        print(logs)

        ssh.close()
        print("\n" + "="*80)
        print("部署完成！")
        print("="*80)
        print("\n新功能:")
        print("1. 平台下拉选择 - 支持9个常用平台 + 自定义")
        print("2. 登录测试 - 点击测试按钮验证账号")
        print("3. 状态显示 - 显示账号验证状态（已验证/失败/未测试）")
        print("\n访问 http://39.105.12.124:8080")
        print("点击右上角【账号配置】按钮测试新功能")

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    deploy()
