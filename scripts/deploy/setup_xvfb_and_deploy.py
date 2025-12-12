#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安装xvfb并配置systemd服务以支持Chrome headless
"""
import paramiko
import time

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

def setup():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"Connecting to {SERVER_HOST}...")
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("Connected!\n")

        # 1. 安装xvfb
        print("="*80)
        print("1. Installing xvfb (virtual framebuffer):")
        print("="*80)
        stdin, stdout, stderr = ssh.exec_command("sudo yum install -y xorg-x11-server-Xvfb || sudo apt-get install -y xvfb", timeout=120)
        output = stdout.read().decode('utf-8', errors='ignore')
        print(output[-500:] if len(output) > 500 else output)

        # 2. 启动Xvfb服务
        print("\n" + "="*80)
        print("2. Starting Xvfb on display :99:")
        print("="*80)

        # 创建xvfb systemd服务
        xvfb_service = """[Unit]
Description=X Virtual Frame Buffer Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
"""

        # 上传xvfb服务文件
        stdin, stdout, stderr = ssh.exec_command(f"sudo bash -c 'cat > /etc/systemd/system/xvfb.service << EOF\n{xvfb_service}\nEOF'")
        stdout.read()

        # 启动并enable xvfb服务
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl daemon-reload && sudo systemctl enable xvfb && sudo systemctl restart xvfb")
        stdout.read()
        time.sleep(2)

        # 检查xvfb状态
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl status xvfb --no-pager -n 5")
        status = stdout.read().decode('utf-8', errors='ignore')
        print(status)

        # 3. 更新topn服务以包含DISPLAY环境变量
        print("\n" + "="*80)
        print("3. Updating topn service with DISPLAY environment:")
        print("="*80)

        # 读取现有服务文件
        stdin, stdout, stderr = ssh.exec_command("cat /etc/systemd/system/topn.service")
        service_content = stdout.read().decode('utf-8', errors='ignore')

        # 检查是否已经有Environment设置
        if 'Environment=' not in service_content or 'DISPLAY' not in service_content:
            # 在[Service]部分添加DISPLAY环境变量
            lines = service_content.split('\n')
            new_lines = []
            for line in lines:
                new_lines.append(line)
                if line.strip() == '[Service]':
                    new_lines.append('Environment="DISPLAY=:99"')

            new_service_content = '\n'.join(new_lines)

            # 写入新的服务文件
            stdin, stdout, stderr = ssh.exec_command(f"sudo bash -c 'cat > /etc/systemd/system/topn.service << \"EOF\"\n{new_service_content}\nEOF'")
            stdout.read()
            print("Added DISPLAY=:99 to topn.service")
        else:
            print("DISPLAY already configured in topn.service")

        # 4. 上传更新的login_tester.py
        print("\n" + "="*80)
        print("4. Uploading updated login_tester.py:")
        print("="*80)

        sftp = ssh.open_sftp()
        local_file = "D:\\work\\code\\TOP_N\\backend\\login_tester.py"
        remote_file = "/home/u_topn/TOP_N/backend/login_tester.py"

        print(f"Uploading {local_file}...")
        sftp.put(local_file, remote_file)
        sftp.close()
        print("Upload complete!")

        # 5. 重启topn服务
        print("\n" + "="*80)
        print("5. Restarting topn service:")
        print("="*80)
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl daemon-reload && sudo systemctl restart topn")
        stdout.read()
        time.sleep(3)

        # 检查服务状态
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl status topn --no-pager -n 10")
        status = stdout.read().decode('utf-8', errors='ignore')
        print(status)

        # 6. 测试WebDriver初始化
        print("\n" + "="*80)
        print("6. Testing WebDriver with xvfb:")
        print("="*80)
        test_script = """
cd /home/u_topn/TOP_N/backend
timeout 30 /home/u_topn/TOP_N/venv/bin/python << 'EOF'
import sys
import os
sys.path.insert(0, '/home/u_topn/TOP_N/backend')

print(f"DISPLAY: {os.environ.get('DISPLAY', 'Not set')}")

from login_tester import LoginTester
tester = LoginTester(headless=True)

result = tester.init_driver()
print(f"Init result: {result}")

if tester.driver:
    tester.close_driver()
    print("SUCCESS: WebDriver initialized!")
else:
    print("FAILED: WebDriver not initialized")
EOF
"""
        stdin, stdout, stderr = ssh.exec_command(test_script, timeout=45)
        time.sleep(3)

        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')

        if output:
            print(output)
        if error:
            print("Stderr:", error)

        ssh.close()

        print("\n" + "="*80)
        print("SETUP COMPLETE!")
        print("="*80)
        print("\nXvfb has been installed and configured")
        print("DISPLAY environment variable added to topn service")
        print("Updated login_tester.py deployed")
        print("\nTest at: http://39.105.12.124:8080")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    setup()
