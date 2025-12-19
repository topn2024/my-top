#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sqlite3
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB_PATH = '../data/topn.db'
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 获取所有表名
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print('=' * 60)
print('数据库中的所有表及记录数：')
print('=' * 60)

for table in tables:
    table_name = table[0]
    cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
    count = cursor.fetchone()[0]
    print(f'{table_name:30} : {count:>6} 条记录')

# 重点检查publish_tasks表
print('\n' + '=' * 60)
print('publish_tasks 表数据详情：')
print('=' * 60)

try:
    cursor.execute('SELECT COUNT(*) FROM publish_tasks')
    total = cursor.fetchone()[0]
    print(f'总记录数: {total}')

    if total > 0:
        cursor.execute('''
            SELECT id, task_id, user_id, article_title, platform, status, result_url
            FROM publish_tasks
            ORDER BY created_at DESC
            LIMIT 5
        ''')
        print('\n最近5条任务记录：')
        for row in cursor.fetchall():
            print(f'  ID={row[0]}, task_id={row[1][:20]}..., user={row[2]}, title={row[3][:30] if row[3] else "NULL"}...')
            print(f'    platform={row[4]}, status={row[5]}, url={row[6][:50] if row[6] else "NULL"}')
except Exception as e:
    print(f'错误: {e}')

conn.close()
