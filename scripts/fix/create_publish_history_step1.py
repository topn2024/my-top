#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
步骤1: 创建发布历史数据库
"""
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

DB_INIT_SCRIPT = """import sqlite3
import os
from datetime import datetime

# 创建数据库
db_path = '/home/u_topn/TOP_N/backend/publish_history.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 创建发布历史表
cursor.execute('''
CREATE TABLE IF NOT EXISTS publish_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT,
    platform TEXT NOT NULL,
    account_username TEXT NOT NULL,
    status TEXT NOT NULL,
    article_url TEXT,
    error_message TEXT,
    publish_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    article_type TEXT,
    word_count INTEGER,
    publish_user TEXT DEFAULT 'system'
)
''')

# 创建索引
cursor.execute('CREATE INDEX IF NOT EXISTS idx_publish_time ON publish_history(publish_time DESC)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON publish_history(status)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_platform ON publish_history(platform)')

conn.commit()
conn.close()

print("✓ 数据库初始化完成")
"""

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
    print("✓ SSH连接成功\n")

    # 创建数据库初始化脚本
    print("创建数据库初始化脚本...")
    cmd = f"cat > /home/u_topn/TOP_N/backend/init_publish_history_db.py << 'ENDPY'\n{DB_INIT_SCRIPT}\nENDPY"
    ssh.exec_command(cmd, timeout=10)
    print("✓ 脚本已创建")

    # 执行数据库初始化
    print("\n执行数据库初始化...")
    cmd = "cd /home/u_topn/TOP_N/backend && python3 init_publish_history_db.py"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    print(stdout.read().decode('utf-8'))

    print("\n✅ 步骤1完成: 数据库已创建")

    ssh.close()

except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
