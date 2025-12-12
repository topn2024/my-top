#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
在服务器上直接下载ChromeDriver 143
"""
import paramiko
import time

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

def install_chromedriver_143():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"Connecting to {SERVER_HOST}...")
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("Connected!\n")

        # 尝试多个ChromeDriver 143版本的镜像
        commands = [
            ("Clean old files", "cd /home/u_topn && rm -f chromedriver* LICENSE.chromedriver"),
            # 尝试阿里云镜像
            ("Download ChromeDriver 143 (Alibaba mirror)",
             "cd /home/u_topn && wget -O chromedriver.zip 'https://registry.npmmirror.com/-/binary/chromedriver/143.0.6999.0/chromedriver_linux64.zip'"),
            ("Unzip", "cd /home/u_topn && unzip -o chromedriver.zip"),
            ("Make executable", "chmod +x /home/u_topn/chromedriver"),
            ("Verify version", "/home/u_topn/chromedriver --version"),
            ("Clean up zip", "rm -f /home/u_topn/chromedriver.zip"),
        ]

        for step_name, cmd in commands:
            print(f"{'='*60}")
            print(f"{step_name}")
            print('='*60)

            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
            output = stdout.read().decode('utf-8', errors='ignore').strip()
            error = stderr.read().decode('utf-8', errors='ignore').strip()

            if output:
                # 只显示最后几行
                lines = output.split('\n')
                if len(lines) > 10:
                    print('\n'.join(lines[-10:]))
                else:
                    print(output)

            if error and "saving to" not in error.lower() and "inflating" not in error.lower():
                print(f"Note: {error[:200]}")

            print("[OK]\n")
            time.sleep(0.5)

        # 重启服务
        print("="*60)
        print("Restarting service")
        print("="*60)
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl restart topn")
        stdout.read()
        time.sleep(3)

        print("\nChecking service...")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl status topn --no-pager -n 3")
        status = stdout.read().decode('utf-8', errors='ignore')
        print(status)

        ssh.close()

        print("\n" + "="*80)
        print("ChromeDriver installation complete!")
        print("="*80)
        print("\nPlease test login at: http://39.105.12.124:8080")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    install_chromedriver_143()
