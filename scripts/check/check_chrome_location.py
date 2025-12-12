#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查看Chrome的实际安装位置
"""
import paramiko

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

def check_location():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"Connecting to {SERVER_HOST}...")
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("Connected!\n")

        print("="*80)
        print("Chrome Installation Locations:")
        print("="*80)

        # 1. 查看/usr/bin/google-chrome的链接
        print("\n1. /usr/bin/google-chrome (symbolic link):")
        stdin, stdout, stderr = ssh.exec_command("ls -l /usr/bin/google-chrome")
        result = stdout.read().decode('utf-8', errors='ignore')
        print(result)

        # 2. 查看实际指向
        print("2. Following the symbolic link chain:")
        stdin, stdout, stderr = ssh.exec_command("readlink -f /usr/bin/google-chrome")
        real_path = stdout.read().decode('utf-8', errors='ignore').strip()
        print(f"Real path: {real_path}")

        # 3. 查看Chrome的安装目录
        print("\n3. Chrome installation directory:")
        stdin, stdout, stderr = ssh.exec_command("ls -l /opt/google/chrome/ 2>/dev/null || ls -l /usr/share/google/chrome/ 2>/dev/null || echo 'Not found'")
        chrome_dir = stdout.read().decode('utf-8', errors='ignore')
        print(chrome_dir[:500])

        # 4. 查看二进制文件位置
        print("\n4. Chrome binary file:")
        stdin, stdout, stderr = ssh.exec_command("which google-chrome")
        which_result = stdout.read().decode('utf-8', errors='ignore').strip()
        print(f"which google-chrome: {which_result}")

        # 5. 查看Chrome相关文件
        print("\n5. Chrome related files:")
        stdin, stdout, stderr = ssh.exec_command("rpm -ql google-chrome-stable 2>/dev/null | head -20 || dpkg -L google-chrome-stable 2>/dev/null | head -20")
        files = stdout.read().decode('utf-8', errors='ignore')
        print(files)

        ssh.close()

        print("\n" + "="*80)
        print("CHECK COMPLETE")
        print("="*80)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_location()
