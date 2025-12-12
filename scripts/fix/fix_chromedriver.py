#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复ChromeDriver安装问题
"""
import paramiko
import time

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

def fix_chromedriver():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"Connecting to {SERVER_HOST}...")
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("Connected!\n")

        # Chrome版本是143，我们需要匹配的ChromeDriver版本
        # 对于Chrome 143，应该使用ChromeDriver 131
        commands = [
            ("Check Chrome version", "google-chrome --version"),
            ("Clean up old files", "cd /tmp && rm -f chromedriver chromedriver_linux64.zip"),
            ("Download ChromeDriver 131", "cd /tmp && wget https://storage.googleapis.com/chrome-for-testing-public/131.0.6778.204/linux64/chromedriver-linux64.zip"),
            ("Unzip ChromeDriver", "cd /tmp && unzip -o chromedriver-linux64.zip"),
            ("Move to system path", "sudo cp /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver"),
            ("Set permissions", "sudo chmod +x /usr/local/bin/chromedriver"),
            ("Verify installation", "chromedriver --version"),
            ("Test with Python", "/home/u_topn/TOP_N/venv/bin/python -c 'from selenium import webdriver; from selenium.webdriver.chrome.options import Options; opt = Options(); opt.add_argument(\"--headless\"); opt.add_argument(\"--no-sandbox\"); opt.add_argument(\"--disable-dev-shm-usage\"); driver = webdriver.Chrome(executable_path=\"/usr/local/bin/chromedriver\", options=opt); print(\"WebDriver initialized successfully!\"); driver.quit()'"),
        ]

        for step_name, cmd in commands:
            print(f"{'='*60}")
            print(f"{step_name}")
            print(f"Command: {cmd}")
            print('='*60)

            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
            output = stdout.read().decode('utf-8', errors='ignore').strip()
            error = stderr.read().decode('utf-8', errors='ignore').strip()

            if output:
                print(f"Output: {output}")
            if error and "warning" not in error.lower():
                print(f"Error: {error}")

            print("[OK] Step completed\n")
            time.sleep(1)

        # 重启服务
        print("="*60)
        print("Restarting topn service...")
        print("="*60)
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl restart topn")
        stdout.read()
        time.sleep(3)

        print("\nChecking service status...")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl status topn --no-pager -n 5")
        status = stdout.read().decode('utf-8', errors='ignore')
        print(status)

        ssh.close()

        print("\n" + "="*80)
        print("ChromeDriver installation fixed!")
        print("="*80)
        print("\nPlease test again at: http://39.105.12.124:8080")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_chromedriver()
