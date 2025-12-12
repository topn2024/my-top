#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Install Selenium Python package with retry and Aliyun mirror
"""
import paramiko
import time

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

def install_selenium_retry():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"Connecting to server {SERVER_HOST}...")
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("Connected successfully!")

        # Try installing with Aliyun mirror for better connectivity in China
        commands = [
            ("Install using Aliyun mirror",
             "/home/u_topn/TOP_N/venv/bin/pip install -i https://mirrors.aliyun.com/pypi/simple/ selenium"),
            ("Verify installation",
             "/home/u_topn/TOP_N/venv/bin/python -c 'import selenium; print(\"Selenium version:\", selenium.__version__)'"),
        ]

        for step_name, command in commands:
            print(f"\n{step_name}...")
            stdin, stdout, stderr = ssh.exec_command(command, timeout=180)
            output = stdout.read().decode('utf-8', errors='ignore')
            error = stderr.read().decode('utf-8', errors='ignore')

            if output:
                print("Output:", output.strip())
            if error and "successfully installed" not in error.lower() and "warning" not in error.lower():
                print("Error:", error.strip())

        print("\nRestarting topn service...")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl restart topn")
        stdout.read()

        time.sleep(3)

        print("\nChecking service status...")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl status topn --no-pager -n 5")
        status = stdout.read().decode('utf-8', errors='ignore')
        print(status)

        print("\nChecking logs for Selenium...")
        stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u topn -n 10 --no-pager | grep -i selenium")
        logs = stdout.read().decode('utf-8', errors='ignore')
        if logs:
            print("Selenium logs:", logs)
        else:
            print("No Selenium-related logs found (this is normal if import succeeded)")

        ssh.close()

        print("\n" + "="*80)
        print("Installation complete!")
        print("="*80)
        print("\nYou can now test real website login functionality at:")
        print("http://39.105.12.124:8080")
        print("\nClick [Account Configuration] -> Add account -> Click [Test] button")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    install_selenium_retry()
