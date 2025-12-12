#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
在服务器上安装Selenium和Chrome环境
"""
import paramiko

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

def install_selenium():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"正在连接服务器 {SERVER_HOST}...")
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("服务器连接成功！")

        commands = [
            # 1. 安装Chrome浏览器
            ("安装Chrome依赖", "sudo yum install -y wget unzip"),
            ("下载Chrome", "cd /tmp && wget https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm"),
            ("安装Chrome", "sudo yum install -y /tmp/google-chrome-stable_current_x86_64.rpm"),
            ("验证Chrome", "google-chrome --version"),

            # 2. 安装ChromeDriver
            ("获取Chrome版本", "google-chrome --version | grep -oP '\\d+\\.\\d+\\.\\d+' | head -1"),
            ("下载ChromeDriver", "cd /tmp && wget https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip"),
            ("解压ChromeDriver", "cd /tmp && unzip -o chromedriver_linux64.zip"),
            ("移动ChromeDriver", "sudo mv /tmp/chromedriver /usr/local/bin/"),
            ("设置权限", "sudo chmod +x /usr/local/bin/chromedriver"),
            ("验证ChromeDriver", "chromedriver --version"),

            # 3. 在虚拟环境中安装Selenium
            ("安装Selenium", "/home/u_topn/TOP_N/venv/bin/pip install selenium"),
            ("验证Selenium", "/home/u_topn/TOP_N/venv/bin/python -c 'import selenium; print(selenium.__version__)'"),
        ]

        for step_name, command in commands:
            print(f"\n{'='*60}")
            print(f"执行: {step_name}")
            print(f"命令: {command}")
            print('='*60)

            stdin, stdout, stderr = ssh.exec_command(command, timeout=120)
            output = stdout.read().decode('utf-8', errors='ignore')
            error = stderr.read().decode('utf-8', errors='ignore')

            if output:
                print("输出:", output)
            if error and "warning" not in error.lower():
                print("错误:", error)

            print(f"[OK] {step_name} 完成")

        print("\n" + "="*80)
        print("Selenium环境安装完成！")
        print("="*80)

        ssh.close()

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("""
    ==========================================
    服务器Selenium环境安装脚本
    ==========================================

    将安装以下组件:
    1. Google Chrome 浏览器
    2. ChromeDriver
    3. Python Selenium 库

    注意: 此过程需要较长时间，请耐心等待
    ==========================================
    """)

    print("开始安装...")
    install_selenium()
