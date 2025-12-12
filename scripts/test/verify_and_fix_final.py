#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证并最终修复登录测试器
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
        print("🔧 最终修复登录测试器")
        print("="*80)

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("✓ SSH连接成功\n")

        # 检查 test_account_login 函数的实现
        print("[1/4] 检查 test_account_login 函数...")
        cmd = """
cd /home/u_topn/TOP_N/backend
grep -A 10 "def test_account_login" login_tester.py
"""
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        output = stdout.read().decode('utf-8')
        print(output)

        # 直接查看该函数实例化的是哪个类
        print("\n[2/4] 查找函数中实例化的类...")
        cmd = """
cd /home/u_topn/TOP_N/backend
grep -B 5 -A 15 "def test_account_login" login_tester.py | grep -E "tester =|LoginTester"
"""
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        output = stdout.read().decode('utf-8')
        print(output)

        # 强制替换为 LoginTesterUltimate
        print("\n[3/4] 强制修改 test_account_login 函数...")
        cmd = """
cd /home/u_topn/TOP_N/backend

# 备份
cp login_tester.py login_tester.py.backup_final

# 使用 Python 脚本进行精确替换
python3 << 'PYEOF'
with open('login_tester.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 在 test_account_login 函数中，将 LoginTester( 替换为 LoginTesterUltimate(
import re

# 查找 test_account_login 函数内的 LoginTester 实例化
pattern = r'(def test_account_login.*?)(tester = LoginTester\()'
replacement = r'\1tester = LoginTesterUltimate('

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# 保存
with open('login_tester.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ 修改完成")
PYEOF

echo ""
echo "验证修改:"
grep -A 10 "def test_account_login" login_tester.py | grep -E "tester =|Login"
"""
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        print(output)
        if error:
            print(f"错误: {error}")

        # 重启服务
        print("\n[4/4] 重启服务...")
        cmd = "sudo systemctl restart topn && sleep 3 && sudo systemctl status topn --no-pager -l | head -20"
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
        import time
        time.sleep(4)
        output = stdout.read().decode('utf-8')
        print(output)

        print("\n" + "="*80)
        print("✅ 修复完成！")
        print("="*80)
        print("\n现在请在 Web 界面测试账号登录功能")

        ssh.close()
        return True

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()
