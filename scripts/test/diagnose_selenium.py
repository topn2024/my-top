#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断Selenium环境问题
"""
import paramiko

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

def diagnose():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"Connecting to {SERVER_HOST}...")
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("Connected!\n")

        # 检查项目列表
        checks = [
            ("Chrome installation", "google-chrome --version"),
            ("ChromeDriver installation", "chromedriver --version"),
            ("ChromeDriver location", "which chromedriver"),
            ("Selenium Python package", "/home/u_topn/TOP_N/venv/bin/python -c 'import selenium; print(selenium.__version__)'"),
            ("Test basic WebDriver import", "/home/u_topn/TOP_N/venv/bin/python -c 'from selenium import webdriver; print(\"Import OK\")'"),
            ("Check Chrome binary", "which google-chrome"),
            ("Test WebDriver init", "/home/u_topn/TOP_N/venv/bin/python -c 'from selenium import webdriver; from selenium.webdriver.chrome.options import Options; opt = Options(); opt.add_argument(\"--headless\"); opt.add_argument(\"--no-sandbox\"); opt.add_argument(\"--disable-dev-shm-usage\"); driver = webdriver.Chrome(options=opt); print(\"WebDriver init OK\"); driver.quit()'"),
        ]

        for name, cmd in checks:
            print(f"{'='*60}")
            print(f"Checking: {name}")
            print(f"Command: {cmd}")
            print('='*60)

            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
            output = stdout.read().decode('utf-8', errors='ignore').strip()
            error = stderr.read().decode('utf-8', errors='ignore').strip()

            if output:
                print(f"[OK] {output}")
            if error:
                print(f"[ERROR] {error}")
            print()

        # 查看最近的应用日志
        print("="*60)
        print("Recent application logs:")
        print("="*60)
        stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u topn -n 30 --no-pager | grep -i -A 5 -B 5 'selenium\\|chrome\\|webdriver'")
        logs = stdout.read().decode('utf-8', errors='ignore')
        if logs:
            print(logs)
        else:
            print("No Selenium/Chrome related logs found")

        ssh.close()

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnose()
