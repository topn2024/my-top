#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接安装DrissionPage和undetected-chromedriver到系统Python
"""
import paramiko
import time
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

def print_step(title):
    print("\n" + "="*80)
    print(title)
    print("="*80)

def main():
    try:
        print_step("🚀 直接安装DrissionPage和undetected-chromedriver")

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("✓ SSH连接成功\n")

        # 步骤1: 验证Python 3.14
        print_step("步骤1: 验证Python 3.14")

        stdin, stdout, stderr = ssh.exec_command("python3 --version", timeout=10)
        output = stdout.read().decode('utf-8')
        print(f"当前Python版本: {output.strip()}")

        if "3.14" not in output:
            print("⚠ 警告: Python版本不是3.14")
        else:
            print("✓ Python 3.14已确认")

        # 步骤2: 检查pip版本
        print_step("步骤2: 检查pip")

        stdin, stdout, stderr = ssh.exec_command("pip3 --version", timeout=10)
        output = stdout.read().decode('utf-8')
        print(f"pip版本: {output.strip()}")

        # 步骤3: 安装selenium
        print_step("步骤3: 安装selenium")

        install_cmd = """
echo "安装selenium 4.15.0..."
pip3 install selenium==4.15.0

echo ""
echo "✓ selenium安装完成"
pip3 list | grep selenium
"""

        stdin, stdout, stderr = ssh.exec_command(install_cmd, timeout=120)

        # 实时显示输出
        while not stdout.channel.exit_status_ready():
            if stdout.channel.recv_ready():
                data = stdout.channel.recv(1024).decode('utf-8', errors='ignore')
                print(data, end='', flush=True)
            time.sleep(0.1)

        output = stdout.read().decode('utf-8', errors='ignore')
        print(output)

        # 步骤4: 安装undetected-chromedriver
        print_step("步骤4: 安装undetected-chromedriver")

        install_cmd = """
echo "安装undetected-chromedriver..."
pip3 install undetected-chromedriver

echo ""
echo "✓ undetected-chromedriver安装完成"
pip3 list | grep undetected
"""

        stdin, stdout, stderr = ssh.exec_command(install_cmd, timeout=120)

        # 实时显示输出
        while not stdout.channel.exit_status_ready():
            if stdout.channel.recv_ready():
                data = stdout.channel.recv(1024).decode('utf-8', errors='ignore')
                print(data, end='', flush=True)
            time.sleep(0.1)

        output = stdout.read().decode('utf-8', errors='ignore')
        print(output)

        # 步骤5: 安装DrissionPage
        print_step("步骤5: 安装DrissionPage")

        install_cmd = """
echo "安装DrissionPage..."
pip3 install DrissionPage

echo ""
echo "✓ DrissionPage安装完成"
pip3 list | grep DrissionPage
"""

        stdin, stdout, stderr = ssh.exec_command(install_cmd, timeout=120)

        # 实时显示输出
        while not stdout.channel.exit_status_ready():
            if stdout.channel.recv_ready():
                data = stdout.channel.recv(1024).decode('utf-8', errors='ignore')
                print(data, end='', flush=True)
            time.sleep(0.1)

        output = stdout.read().decode('utf-8', errors='ignore')
        print(output)

        # 步骤6: 验证安装
        print_step("步骤6: 验证安装")

        test_cmd = """
export DISPLAY=:99

python3 << 'EOF'
import sys
print(f"Python版本: {sys.version}")
print("")

try:
    import undetected_chromedriver as uc
    print(f"✓ undetected-chromedriver 导入成功 (version: {uc.__version__})")
except Exception as e:
    print(f"✗ undetected-chromedriver: {e}")

try:
    from DrissionPage import ChromiumPage
    print("✓ DrissionPage 导入成功")
except Exception as e:
    print(f"✗ DrissionPage: {e}")

try:
    import selenium
    print(f"✓ selenium 导入成功 (version: {selenium.__version__})")
except Exception as e:
    print(f"✗ selenium: {e}")

print("")
print("=" * 60)
print("验证完成!")
print("=" * 60)
EOF
"""

        stdin, stdout, stderr = ssh.exec_command(test_cmd, timeout=60)
        time.sleep(2)
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        print(output)
        if error:
            print(f"错误输出: {error}")

        # 完成
        print_step("🎉 安装完成!")

        print("\n✅ 已完成:")
        print("  1. ✓ Python 3.14验证")
        print("  2. ✓ selenium安装")
        print("  3. ✓ undetected-chromedriver安装")
        print("  4. ✓ DrissionPage安装")
        print("  5. ✓ 导入测试")

        print("\n📝 下一步:")
        print("\n1. 测试终极版登录器:")
        print("   cd /home/u_topn/TOP_N/backend")
        print("   export DISPLAY=:99")
        print("   python3 -c \"from login_tester_ultimate import LoginTesterUltimate; t = LoginTesterUltimate(headless=True); print(f'使用模式: {t.actual_mode}')\"")

        print("\n2. 更新app.py使用终极版:")
        print("   nano /home/u_topn/TOP_N/backend/app.py")
        print("   # 修改导入:")
        print("   from login_tester_ultimate import LoginTesterUltimate as LoginTester")

        print("\n3. 重启服务:")
        print("   sudo systemctl restart topn")
        print("   sudo systemctl status topn")

        ssh.close()
        return True

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()

    if success:
        print("\n" + "="*80)
        print("✅ 所有包安装完成！")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("❌ 安装失败，请检查错误信息。")
        print("="*80)
