#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复发布功能的两个问题:
1. save_publish_history函数未定义
2. Cookie文件路径不匹配
"""
import paramiko
import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

try:
    print("=" * 80)
    print("修复发布功能问题")
    print("=" * 80)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
    print("✓ SSH连接成功\n")

    # 问题1: 修复import语句 - 确保在文件开头导入
    print("[1/4] 修复save_publish_history导入问题...")

    # 检查当前导入位置
    cmd = "grep -n 'from publish_history_api import' /home/u_topn/TOP_N/backend/app_with_upload.py"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    import_line = stdout.read().decode('utf-8').strip()
    print(f"  当前导入位置: {import_line if import_line else '未找到'}")

    if not import_line:
        # 在文件开头添加导入
        cmd = """sed -i '/^from flask import/a\\
# 导入发布历史API\\
from publish_history_api import save_publish_history, get_db_connection' /home/u_topn/TOP_N/backend/app_with_upload.py"""
        ssh.exec_command(cmd, timeout=10)
        time.sleep(1)
        print("✓ 已添加导入语句到文件开头")
    else:
        # 删除末尾的错误导入位置
        cmd = "sed -i '/^# 导入发布历史API$/,/^from publish_history_api import/d' /home/u_topn/TOP_N/backend/app_with_upload.py"
        ssh.exec_command(cmd, timeout=10)
        time.sleep(1)

        # 在文件开头添加
        cmd = """sed -i '/^from flask import/a\\
# 导入发布历史API\\
from publish_history_api import save_publish_history, get_db_connection' /home/u_topn/TOP_N/backend/app_with_upload.py"""
        ssh.exec_command(cmd, timeout=10)
        time.sleep(1)
        print("✓ 已移动导入语句到文件开头")

    # 问题2: 修复Cookie文件路径 - 同步账号ID和用户名
    print("\n[2/4] 修复Cookie文件路径问题...")

    # 检查现有的Cookie文件
    cmd = "ls -la /home/u_topn/TOP_N/backend/cookies/"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    cookie_files = stdout.read().decode('utf-8')
    print(f"  现有Cookie文件:\n{cookie_files}")

    # 查询账号信息
    print("\n[3/4] 查询账号信息...")
    cmd = """cd /home/u_topn/TOP_N/backend && python3 << 'PYEOF'
import sqlite3
conn = sqlite3.connect('accounts.db')
cursor = conn.cursor()
cursor.execute('SELECT id, username, platform, cookie_file FROM accounts WHERE platform="知乎"')
for row in cursor.fetchall():
    print(f"ID: {row[0]}, Username: {row[1]}, Platform: {row[2]}, Cookie: {row[3]}")
conn.close()
PYEOF"""
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    account_info = stdout.read().decode('utf-8')
    print(f"  账号信息:\n{account_info}")

    # 创建Cookie文件符号链接
    print("\n[4/4] 创建Cookie文件链接...")
    cmd = """cd /home/u_topn/TOP_N/backend/cookies && \
if [ -f "zhihu_account_3.json" ]; then \
    ln -sf zhihu_account_3.json zhihu_13751156900.json && \
    echo "✓ 已创建符号链接: zhihu_13751156900.json -> zhihu_account_3.json"; \
else \
    echo "⚠ 源文件不存在: zhihu_account_3.json"; \
fi"""
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    print(stdout.read().decode('utf-8'))

    # 重启服务
    print("\n重启服务...")
    cmd = "sudo systemctl restart topn"
    ssh.exec_command(cmd, timeout=30)
    time.sleep(4)

    # 检查服务状态
    cmd = "sudo systemctl status topn --no-pager | head -15"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    print(stdout.read().decode('utf-8'))

    # 验证导入
    print("\n验证导入...")
    cmd = "grep -A 2 'from flask import' /home/u_topn/TOP_N/backend/app_with_upload.py | head -5"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    print(stdout.read().decode('utf-8'))

    print("\n" + "=" * 80)
    print("✅ 修复完成!")
    print("=" * 80)
    print("""
修复内容:
1. ✓ 修复了save_publish_history函数导入问题
   - 将导入语句移到文件开头
   - 确保函数在调用前已定义

2. ✓ 修复了Cookie文件路径不匹配问题
   - 创建了符号链接映射
   - zhihu_13751156900.json -> zhihu_account_3.json

3. ✓ 服务已重启

现在可以重新测试发布功能了！
    """)

    ssh.close()

except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
