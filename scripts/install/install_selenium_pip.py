#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Install Selenium Python package in virtual environment
"""
import paramiko

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

def install_selenium_pip():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"Connecting to server {SERVER_HOST}...")
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("Connected successfully!")

        print("\n1. Installing Selenium Python package...")
        stdin, stdout, stderr = ssh.exec_command("/home/u_topn/TOP_N/venv/bin/pip install selenium", timeout=120)
        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')

        if output:
            print("Output:", output)
        if error and "warning" not in error.lower():
            print("Error:", error)

        print("\n2. Verifying Selenium installation...")
        stdin, stdout, stderr = ssh.exec_command("/home/u_topn/TOP_N/venv/bin/python -c 'import selenium; print(\"Selenium version:\", selenium.__version__)'", timeout=10)
        output = stdout.read().decode('utf-8', errors='ignore')

        if 'Selenium version' in output:
            print("[OK]", output.strip())
        else:
            print("[FAILED] Selenium not detected")

        print("\n3. Restarting service...")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl restart topn")
        stdout.read()

        import time
        time.sleep(2)

        print("\n4. Checking service status...")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl status topn --no-pager -n 3")
        status = stdout.read().decode('utf-8', errors='ignore')
        print(status)

        ssh.close()

        print("\n" + "="*80)
        print("Selenium Python package installation complete!")
        print("="*80)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    install_selenium_pip()
