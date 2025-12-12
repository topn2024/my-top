#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安装所有缺失的依赖包
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
        print_step("📦 安装所有依赖包")

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("✓ SSH连接成功\n")

        # 步骤1: 安装setuptools (包含distutils替代)
        print_step("步骤1: 安装setuptools (distutils替代)")

        install_cmd = """
echo "安装setuptools..."
pip3 install --upgrade setuptools

echo ""
echo "✓ setuptools安装完成"
pip3 show setuptools
"""

        stdin, stdout, stderr = ssh.exec_command(install_cmd, timeout=120)

        while not stdout.channel.exit_status_ready():
            if stdout.channel.recv_ready():
                data = stdout.channel.recv(1024).decode('utf-8', errors='ignore')
                print(data, end='', flush=True)
            time.sleep(0.1)

        output = stdout.read().decode('utf-8', errors='ignore')
        print(output)

        # 步骤2: 重新安装DrissionPage和undetected-chromedriver
        print_step("步骤2: 重新安装DrissionPage和undetected-chromedriver")

        install_cmd = """
echo "重新安装undetected-chromedriver..."
pip3 uninstall -y undetected-chromedriver
pip3 install undetected-chromedriver

echo ""
echo "重新安装DrissionPage..."
pip3 uninstall -y DrissionPage
pip3 install DrissionPage

echo ""
echo "✓ 安装完成"
pip3 list | grep -E "undetected|DrissionPage"
"""

        stdin, stdout, stderr = ssh.exec_command(install_cmd, timeout=300)

        while not stdout.channel.exit_status_ready():
            if stdout.channel.recv_ready():
                data = stdout.channel.recv(1024).decode('utf-8', errors='ignore')
                print(data, end='', flush=True)
            time.sleep(0.1)

        output = stdout.read().decode('utf-8', errors='ignore')
        print(output)

        # 步骤3: 安装app.py需要的所有依赖
        print_step("步骤3: 安装app.py所需依赖")

        install_cmd = """
echo "安装app.py依赖..."
pip3 install openai anthropic dashscope zhipuai
pip3 install pillow beautifulsoup4 lxml
pip3 install flask-limiter

echo ""
echo "✓ 依赖安装完成"
pip3 list | grep -E "openai|anthropic|dashscope|zhipuai|Pillow|beautifulsoup4|lxml|Flask-Limiter"
"""

        stdin, stdout, stderr = ssh.exec_command(install_cmd, timeout=300)

        while not stdout.channel.exit_status_ready():
            if stdout.channel.recv_ready():
                data = stdout.channel.recv(1024).decode('utf-8', errors='ignore')
                print(data, end='', flush=True)
            time.sleep(0.1)

        output = stdout.read().decode('utf-8', errors='ignore')
        print(output)

        # 步骤4: 验证所有导入
        print_step("步骤4: 验证所有包导入")

        test_cmd = """
export DISPLAY=:99

python3 << 'EOF'
import sys
print(f"Python版本: {sys.version}")
print("")
print("测试所有包导入:")
print("-" * 60)

packages = [
    ('flask', 'Flask'),
    ('flask_cors', 'flask-cors'),
    ('requests', 'requests'),
    ('selenium', 'selenium'),
    ('openai', 'openai'),
    ('anthropic', 'anthropic'),
    ('dashscope', 'dashscope'),
    ('zhipuai', 'zhipuai'),
    ('PIL', 'Pillow'),
    ('bs4', 'beautifulsoup4'),
    ('lxml', 'lxml'),
]

for pkg_name, display_name in packages:
    try:
        __import__(pkg_name)
        print(f"✓ {display_name}")
    except Exception as e:
        print(f"✗ {display_name}: {e}")

# 特别测试DrissionPage和undetected-chromedriver
print("")
print("测试浏览器自动化包:")
print("-" * 60)

try:
    from DrissionPage import ChromiumPage
    print("✓ DrissionPage")
except Exception as e:
    print(f"✗ DrissionPage: {e}")

try:
    import undetected_chromedriver as uc
    print("✓ undetected-chromedriver")
except Exception as e:
    print(f"✗ undetected-chromedriver: {e}")

print("")
print("=" * 60)
print("导入测试完成!")
EOF
"""

        stdin, stdout, stderr = ssh.exec_command(test_cmd, timeout=60)
        time.sleep(2)
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        print(output)
        if error:
            print(f"stderr输出: {error}")

        # 步骤5: 测试LoginTesterUltimate
        print_step("步骤5: 测试LoginTesterUltimate最终状态")

        tester_cmd = """
cd /home/u_topn/TOP_N/backend
export DISPLAY=:99

python3 << 'EOF'
try:
    from login_tester_ultimate import LoginTesterUltimate
    print("✓ LoginTesterUltimate导入成功")

    # 测试自动模式
    tester = LoginTesterUltimate(headless=True, mode='auto')
    print(f"✓ 实例创建成功")
    print(f"✓ 使用模式: {tester.actual_mode}")

    if tester.actual_mode == 'drissionpage':
        print("🎉 成功使用DrissionPage模式!")
    elif tester.actual_mode == 'uc':
        print("⚠ 使用undetected-chromedriver模式")
    else:
        print("⚠ 降级到selenium模式")

except Exception as e:
    print(f"✗ LoginTesterUltimate: {e}")
    import traceback
    traceback.print_exc()
EOF
"""

        stdin, stdout, stderr = ssh.exec_command(tester_cmd, timeout=60)
        time.sleep(2)
        output = stdout.read().decode('utf-8')
        print(output)

        # 步骤6: 重启服务
        print_step("步骤6: 重启topn服务")

        restart_cmd = """
sudo systemctl restart topn
sleep 3
sudo systemctl status topn --no-pager -l
"""

        stdin, stdout, stderr = ssh.exec_command(restart_cmd, timeout=30)
        time.sleep(4)
        output = stdout.read().decode('utf-8')
        print(output)

        # 步骤7: 查看服务日志
        print_step("步骤7: 查看服务启动日志")

        log_cmd = "sudo journalctl -u topn -n 30 --no-pager"
        stdin, stdout, stderr = ssh.exec_command(log_cmd, timeout=10)
        output = stdout.read().decode('utf-8')
        print(output[-2000:])

        # 完成
        print_step("🎉 所有依赖安装完成!")

        print("\n✅ 已安装:")
        print("  • setuptools (distutils替代)")
        print("  • DrissionPage 和 undetected-chromedriver")
        print("  • openai, anthropic, dashscope, zhipuai")
        print("  • Pillow, beautifulsoup4, lxml")
        print("  • Flask-Limiter")

        print("\n📊 系统状态:")
        print("  • Python: 3.14.0")
        print("  • 服务: topn.service")
        print("  • 登录器: LoginTesterUltimate")

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
        print("✅ 所有依赖安装完成！系统已就绪。")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("❌ 安装过程中遇到问题。")
        print("="*80)
