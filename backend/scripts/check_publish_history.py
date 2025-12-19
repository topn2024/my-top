#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 publish_history 表的数据
"""
import sqlite3
import sys
import io

# 设置标准输出为UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB_PATH = '../data/topn.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 查看总记录数
cursor.execute('SELECT COUNT(*) FROM publish_history')
total = cursor.fetchone()[0]
print(f'总记录数: {total}')

# 查看表结构
cursor.execute("PRAGMA table_info(publish_history)")
columns = cursor.fetchall()
print(f'\n表结构:')
for col in columns:
    print(f'  {col[1]} ({col[2]})')

# 查看最近的10条记录
cursor.execute('''
    SELECT id, article_id, article_title, platform, status, published_at
    FROM publish_history
    ORDER BY id DESC
    LIMIT 10
''')
print(f'\n最近10条记录:')
print('ID | Article_ID | Title | Platform | Status | Published_At')
print('-' * 80)
for row in cursor.fetchall():
    print(f'{row[0]} | {row[1]} | {row[2] or "NULL"} | {row[3]} | {row[4]} | {row[5]}')

# 检查有多少记录的 article_title 为 NULL
cursor.execute('SELECT COUNT(*) FROM publish_history WHERE article_title IS NULL')
null_count = cursor.fetchone()[0]
print(f'\narticle_title 为 NULL 的记录数: {null_count}')

# 检查有多少记录的 article_title 不为 NULL
cursor.execute('SELECT COUNT(*) FROM publish_history WHERE article_title IS NOT NULL')
not_null_count = cursor.fetchone()[0]
print(f'article_title 不为 NULL 的记录数: {not_null_count}')

conn.close()
