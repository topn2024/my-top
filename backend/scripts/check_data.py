#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sqlite3
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB_PATH = '../data/topn.db'
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 检查各表的记录数
tables = ['publish_history', 'articles', 'users', 'workflows']

print('数据库记录统计：')
print('=' * 50)
for table in tables:
    try:
        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        count = cursor.fetchone()[0]
        print(f'{table:20} : {count} 条记录')
    except Exception as e:
        print(f'{table:20} : 错误 - {e}')

print('\n' + '=' * 50)
print('publish_history 表数据详情：')
print('=' * 50)

cursor.execute('SELECT COUNT(*) FROM publish_history')
total = cursor.fetchone()[0]

if total > 0:
    cursor.execute('''
        SELECT id, article_id, article_title, platform, status
        FROM publish_history
        ORDER BY id DESC
        LIMIT 5
    ''')
    print('\n最近5条记录：')
    for row in cursor.fetchall():
        print(f'  ID={row[0]}, article_id={row[1]}, title={row[2]}, platform={row[3]}, status={row[4]}')

    cursor.execute('SELECT COUNT(*) FROM publish_history WHERE article_title IS NOT NULL')
    has_title = cursor.fetchone()[0]
    print(f'\n有标题的记录: {has_title}/{total}')

    cursor.execute('SELECT COUNT(*) FROM publish_history WHERE article_content IS NOT NULL')
    has_content = cursor.fetchone()[0]
    print(f'有内容的记录: {has_content}/{total}')
else:
    print('\n表中无数据')

conn.close()
