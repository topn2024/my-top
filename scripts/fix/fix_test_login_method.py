#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 test_account_login 调用正确的方法
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
        print("🔧 修复 test_account_login 方法调用")
        print("="*80)

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("✓ SSH连接成功\n")

        # 修改 test_account_login 函数
        print("[1/2] 修改 test_account_login 函数...")
        cmd = """
cd /home/u_topn/TOP_N/backend

cat > /tmp/fix_method.py << 'PYEOF'
with open('login_tester.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 替换 test_login 为 test_zhihu_login (LoginTesterUltimate 的方法名)
content = content.replace(
    'return tester.test_login(platform, username, password)',
    'return tester.test_zhihu_login(username, password)'
)

with open('login_tester.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ 修改完成")
PYEOF

python3 /tmp/fix_method.py

echo ""
echo "验证修改:"
grep -A 5 "def test_account_login" login_tester.py
"""
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        output = stdout.read().decode('utf-8')
        print(output)

        # 重启服务
        print("\n[2/2] 重启服务...")
        cmd = "sudo systemctl restart topn && sleep 3"
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
        import time
        time.sleep(4)

        print("✓ 服务已重启")
        print("\n" + "="*80)
        print("✅ 修复完成！")
        print("="*80)
        print("\n现在请在 Web 界面测试账号登录功能")
        print("LoginTesterUltimate 使用 DrissionPage 模式")

        ssh.close()
        return True

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()
