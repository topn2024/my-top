#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import paramiko, sys, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER = "39.105.12.124"
USER = "u_topn"
PASSWORD = "TopN@2024"

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=10)
    print(f"✓ 连接成功: {USER}@{SERVER}\n")

    print("1. 检查gunicorn配置文件:")
    stdin, stdout, stderr = ssh.exec_command("cat /home/u_topn/TOP_N/gunicorn_config.py")
    print(stdout.read().decode())

    print("\n2. 检查是否有systemd服务:")
    stdin, stdout, stderr = ssh.exec_command("systemctl --user list-units | grep -i gunicorn || echo 'No systemd service'")
    print(stdout.read().decode())

    print("\n3. 检查是否有supervisor配置:")
    stdin, stdout, stderr = ssh.exec_command("ls -la /etc/supervisor/conf.d/ 2>/dev/null || echo 'No supervisor'")
    print(stdout.read().decode())

    print("\n4. 检查crontab:")
    stdin, stdout, stderr = ssh.exec_command("crontab -l 2>/dev/null | grep -i gunicorn || echo 'No cron jobs'")
    print(stdout.read().decode())

    print("\n5. 查找启动脚本:")
    stdin, stdout, stderr = ssh.exec_command("find /home/u_topn -name '*.sh' -type f 2>/dev/null | head -10")
    print(stdout.read().decode())

    ssh.close()
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
