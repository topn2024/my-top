#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

try:
    print("正在连接服务器...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD)

    print("正在备份旧文件...")
    ssh.exec_command('cp /home/u_topn/TOP_N/backend/qrcode_login.py /home/u_topn/TOP_N/backend/qrcode_login.py.backup_enhanced')

    print("正在上传新文件...")
    sftp = ssh.open_sftp()
    sftp.put('qrcode_login_enhanced.py', '/home/u_topn/TOP_N/backend/qrcode_login.py')
    sftp.close()

    print("上传成功!")

    print("正在重启服务...")
    ssh.exec_command('sudo systemctl restart topn')

    import time
    time.sleep(4)

    print("部署完成!")

    ssh.close()
except Exception as e:
    print(f"错误: {e}")
