#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 API 路由问题
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
        print("🔧 修复 API 路由")
        print("="*80)

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("✓ SSH连接成功\n")

        # 检查当前使用的是哪个 app 文件
        print("[1/4] 检查当前 app 文件...")
        cmd = """
cd /home/u_topn/TOP_N/backend
echo "=== app.py 中的路由 ==="
grep -n "@app.route" app.py | head -20
echo ""
echo "=== app_with_upload.py 中的路由 ==="
grep -n "@app.route" app_with_upload.py | head -20
"""
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        output = stdout.read().decode('utf-8')
        print(output)

        # 创建 accounts.json 文件（如果不存在）
        print("\n[2/4] 创建/检查 accounts.json 文件...")
        cmd = """
cd /home/u_topn/TOP_N/backend
if [ ! -f accounts.json ]; then
    echo '[]' > accounts.json
    echo "✓ 创建了空的 accounts.json 文件"
else
    echo "✓ accounts.json 文件已存在"
fi
cat accounts.json
"""
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        output = stdout.read().decode('utf-8')
        print(output)

        # 检查 app.py 是否有账号管理 API
        print("\n[3/4] 检查 app.py 中的账号管理功能...")
        cmd = """
cd /home/u_topn/TOP_N/backend
grep -A 5 "api/accounts" app.py || echo "未找到 /api/accounts 路由"
"""
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        output = stdout.read().decode('utf-8')
        print(output)

        # 决定是否需要更新服务配置使用 app_with_upload.py
        print("\n[4/4] 建议方案...")
        print("""
发现问题:
1. 当前服务运行的是 app.py
2. /api/accounts 路由不存在（404错误）
3. accounts.json 文件不存在

解决方案:
方案 A: 将服务改为使用 app_with_upload.py（包含完整的账号管理功能）
方案 B: 将 app_with_upload.py 的账号管理代码合并到 app.py

推荐: 方案 A（更简单快速）
""")

        ssh.close()
        return True

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()
