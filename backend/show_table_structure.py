#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
显示 publish_history 表的完整结构
"""
import sqlite3
import sys
import io

# 设置标准输出为UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB_PATH = '../data/topn.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print('=' * 80)
print('publish_history 表结构')
print('=' * 80)

# 获取表结构详细信息
cursor.execute("PRAGMA table_info(publish_history)")
columns = cursor.fetchall()

print(f'\n共 {len(columns)} 个字段：\n')
print(f'{"序号":<6} {"字段名":<25} {"数据类型":<20} {"允许NULL":<12} {"默认值":<15} {"主键"}')
print('-' * 80)

for col in columns:
    cid = col[0]           # 列ID
    name = col[1]          # 列名
    type_ = col[2]         # 数据类型
    notnull = col[3]       # 是否NOT NULL (0=允许NULL, 1=不允许NULL)
    dflt = col[4]          # 默认值
    pk = col[5]            # 是否主键 (0=否, 1=是)

    notnull_str = '否' if notnull == 0 else '是'
    dflt_str = str(dflt) if dflt is not None else '-'
    pk_str = '是' if pk == 1 else '否'

    print(f'{cid:<6} {name:<25} {type_:<20} {notnull_str:<12} {dflt_str:<15} {pk_str}')

# 获取CREATE TABLE语句
print('\n' + '=' * 80)
print('CREATE TABLE 语句：')
print('=' * 80)
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='publish_history'")
create_sql = cursor.fetchone()
if create_sql:
    print(create_sql[0])
else:
    print('未找到CREATE TABLE语句')

# 获取索引信息
print('\n' + '=' * 80)
print('索引信息：')
print('=' * 80)
cursor.execute("PRAGMA index_list(publish_history)")
indexes = cursor.fetchall()
if indexes:
    for idx in indexes:
        print(f'\n索引名: {idx[1]}')
        print(f'  唯一性: {"是" if idx[2] else "否"}')
        cursor.execute(f"PRAGMA index_info({idx[1]})")
        idx_cols = cursor.fetchall()
        cols = [col[2] for col in idx_cols]
        print(f'  列: {", ".join(cols)}')
else:
    print('无索引')

conn.close()

print('\n' + '=' * 80)
