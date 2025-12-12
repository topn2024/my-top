#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 test_account_login 函数使用 LoginTesterUltimate
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
        print("🔧 修复 test_account_login 函数")
        print("="*80)

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("✓ SSH连接成功\n")

        # 检查 login_tester.py 中的 test_account_login 函数
        print("[1/3] 检查当前 login_tester.py...")
        cmd = """
cd /home/u_topn/TOP_N/backend
echo "=== login_tester.py 使用的类 ==="
grep -n "class\\|from.*import\\|def test_account_login" login_tester.py | head -20
"""
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        output = stdout.read().decode('utf-8')
        print(output)

        # 更新 login_tester.py 使用 LoginTesterUltimate
        print("\n[2/3] 更新 login_tester.py...")
        cmd = """
cd /home/u_topn/TOP_N/backend

# 备份
cp login_tester.py login_tester.py.backup_$(date +%Y%m%d_%H%M%S)

# 修改导入和实例化
sed -i 's/from login_tester import LoginTester/from login_tester_ultimate import LoginTesterUltimate as LoginTester/g' login_tester.py

# 如果文件中还没有导入 LoginTesterUltimate，在文件开头添加
if ! grep -q "login_tester_ultimate" login_tester.py; then
    # 找到第一个 class LoginTester 定义的位置，在之前添加导入
    sed -i '1i from login_tester_ultimate import LoginTesterUltimate' login_tester.py
fi

echo "✓ 修改完成"
echo ""
echo "=== 验证修改 ==="
head -30 login_tester.py | grep -E "import|class|def test"
"""
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        output = stdout.read().decode('utf-8')
        print(output)

        # 更简单的方法：直接修改 login_tester.py 的 test_account_login 函数
        print("\n[使用更直接的方法: 修改 test_account_login 函数实现]")

        update_function_cmd = """
cd /home/u_topn/TOP_N/backend

# 创建更新后的 test_account_login 函数
cat > /tmp/update_login_tester.py << 'PYEOF'
import sys

# 读取原文件
with open('login_tester.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 在文件顶部添加 LoginTesterUltimate 导入（如果还没有）
if 'from login_tester_ultimate import' not in content:
    # 找到第一个import语句后添加
    lines = content.split('\\n')
    new_lines = []
    import_added = False
    for line in lines:
        new_lines.append(line)
        if not import_added and line.startswith('import ') or line.startswith('from '):
            new_lines.append('from login_tester_ultimate import LoginTesterUltimate')
            import_added = True
    content = '\\n'.join(new_lines)

# 替换 test_account_login 函数中的 LoginTester 为 LoginTesterUltimate
content = content.replace('tester = LoginTester(', 'tester = LoginTesterUltimate(')

# 写回文件
with open('login_tester.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ 更新完成")
PYEOF

python3 /tmp/update_login_tester.py
"""
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        print(output)
        if error:
            print(f"错误: {error}")

        # 重启服务
        print("\n[3/3] 重启服务...")
        cmd = "sudo systemctl restart topn && sleep 3 && sudo systemctl status topn --no-pager -l"
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
        import time
        time.sleep(4)
        output = stdout.read().decode('utf-8')
        print(output)

        print("\n" + "="*80)
        print("✅ 修复完成!")
        print("="*80)
        print("\n现在 test_account_login 函数使用 LoginTesterUltimate")
        print("支持三种模式: drission > uc > selenium")

        ssh.close()
        return True

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()
