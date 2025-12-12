#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署真实登录测试功能
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
        backup_cmd = "cp /home/u_topn/TOP_N/backend/app_with_upload.py /home/u_topn/TOP_N/backend/app_with_upload.py.backup_selenium_$(date +%Y%m%d_%H%M%S)"
        stdin, stdout, stderr = ssh.exec_command(backup_cmd)
        stdout.read()
        print("备份完成")

        # 上传文件
        print("\n2. 上传文件...")
        files_to_upload = [
            ("D:\\work\\code\\TOP_N\\backend\\app_with_upload.py", "/home/u_topn/TOP_N/backend/app_with_upload.py"),
            ("D:\\work\\code\\TOP_N\\backend\\login_tester.py", "/home/u_topn/TOP_N/backend/login_tester.py"),
        ]

        for local_file, remote_file in files_to_upload:
            print(f"  上传: {os.path.basename(local_file)}")
            sftp.put(local_file, remote_file)

        print("文件上传完成")
        sftp.close()

        # 检查Selenium是否安装
        print("\n3. 检查Selenium环境...")
        stdin, stdout, stderr = ssh.exec_command("/home/u_topn/TOP_N/venv/bin/python -c 'import selenium; print(\"Selenium version:\", selenium.__version__)'", timeout=10)
        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')

        if 'Selenium version' in output:
            print(f"[OK] Selenium installed: {output.strip()}")
            selenium_installed = True
        else:
            print("[X] Selenium not installed")
            print("\n提示: 需要先运行 install_selenium_server.py 安装 Selenium 环境")
            print("      或者手动在服务器上执行:")
            print("      /home/u_topn/TOP_N/venv/bin/pip install selenium")
            selenium_installed = False

        # 重启服务
        print("\n4. 重启topn服务...")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl restart topn")
        stdout.read()
        print("服务重启成功")

        import time
        print("\n5. 等待服务启动...")
        time.sleep(3)

        # 检查服务状态
        print("\n6. 检查服务状态...")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl status topn --no-pager -n 5")
        status = stdout.read().decode('utf-8', errors='ignore')
        print(status)

        # 查看日志
        print("\n7. 查看最新日志...")
        stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u topn -n 15 --no-pager | tail -10")
        logs = stdout.read().decode('utf-8', errors='ignore')
        print(logs)

        ssh.close()

        print("\n" + "="*80)
        print("部署完成！")
        print("="*80)

        if selenium_installed:
            print("\n[OK] Selenium ready for real website login testing")
            print("\nSupported platforms:")
            print("  - Zhihu: Full auto login test")
            print("  - CSDN: Full auto login test")
            print("  - Others: In development...")
        else:
            print("\n[!] Selenium not installed, using basic validation mode")
            print("\n安装Selenium环境步骤:")
            print("1. 运行: python install_selenium_server.py")
            print("2. 或手动在服务器执行:")
            print("   /home/u_topn/TOP_N/venv/bin/pip install selenium")

        print("\n访问 http://39.105.12.124:8080")
        print("点击【账号配置】-> 添加账号 -> 点击【测试】按钮")

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    deploy()
