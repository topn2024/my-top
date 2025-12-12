#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 WebDriver 配置
"""
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

def main():
    try:
        print("="*80)
        print("🔍 检查 WebDriver 配置")
        print("="*80)

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("✓ SSH连接成功\n")

        # 检查 Chrome 是否安装
        print("[1/6] 检查 Chrome 浏览器...")
        cmd = "google-chrome --version 2>&1 || chromium-browser --version 2>&1 || echo 'Chrome未安装'"
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        output = stdout.read().decode('utf-8')
        print(output)

        # 检查 ChromeDriver
        print("\n[2/6] 检查 ChromeDriver...")
        cmd = "chromedriver --version 2>&1 || echo 'ChromeDriver未找到'"
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        output = stdout.read().decode('utf-8')
        print(output)

        # 检查 selenium 版本
        print("\n[3/6] 检查 selenium...")
        cmd = "python3 -c 'import selenium; print(f\"selenium {selenium.__version__}\")' 2>&1"
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        output = stdout.read().decode('utf-8')
        print(output)

        # 检查 undetected-chromedriver
        print("\n[4/6] 检查 undetected-chromedriver...")
        cmd = "python3 -c 'import undetected_chromedriver as uc; print(f\"undetected-chromedriver {uc.__version__}\")' 2>&1"
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        output = stdout.read().decode('utf-8')
        print(output)

        # 检查 login_tester_ultimate.py
        print("\n[5/6] 检查 LoginTesterUltimate 配置...")
        cmd = """
cd /home/u_topn/TOP_N/backend
python3 << 'EOF'
try:
    from login_tester_ultimate import LoginTesterUltimate
    print("✓ LoginTesterUltimate 导入成功")

    # 尝试创建实例看看会用什么模式
    import os
    os.environ['DISPLAY'] = ':99'

    tester = LoginTesterUltimate(headless=True, mode='auto')
    print(f"✓ 自动选择模式: {tester.actual_mode}")

except Exception as e:
    print(f"✗ 错误: {e}")
    import traceback
    traceback.print_exc()
EOF
"""
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        print(output)
        if error:
            print(f"错误输出:\n{error}")

        # 检查 Xvfb 虚拟显示
        print("\n[6/6] 检查 Xvfb 虚拟显示...")
        cmd = "ps aux | grep Xvfb | grep -v grep"
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        output = stdout.read().decode('utf-8')
        if output.strip():
            print("✓ Xvfb 正在运行")
            print(output)
        else:
            print("✗ Xvfb 未运行")

        # 查看最近的服务日志中的错误
        print("\n[查看最近的 WebDriver 相关错误]")
        cmd = "sudo journalctl -u topn -n 50 --no-pager | grep -i -A 3 -B 3 'webdriver\\|chrome\\|driver'"
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        output = stdout.read().decode('utf-8')
        if output.strip():
            print(output[-2000:])
        else:
            print("未发现 WebDriver 相关错误")

        print("\n" + "="*80)
        print("✅ 检查完成")
        print("="*80)

        ssh.close()
        return True

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()
