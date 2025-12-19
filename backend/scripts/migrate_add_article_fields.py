#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：为 publish_history 表添加 article_title 和 article_content 字段
"""
import sqlite3
import sys
import os
import io

# 设置标准输出为UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'topn.db')

def migrate():
    """执行数据库迁移"""
    print(f"数据库路径: {DB_PATH}")

    if not os.path.exists(DB_PATH):
        print(f"错误: 数据库文件不存在: {DB_PATH}")
        return False

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(publish_history)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"当前字段: {columns}")

        # 添加 article_title 字段
        if 'article_title' not in columns:
            print("添加 article_title 字段...")
            cursor.execute("""
                ALTER TABLE publish_history
                ADD COLUMN article_title VARCHAR(500)
            """)
            print("✓ article_title 字段已添加")
        else:
            print("✓ article_title 字段已存在")

        # 添加 article_content 字段
        if 'article_content' not in columns:
            print("添加 article_content 字段...")
            cursor.execute("""
                ALTER TABLE publish_history
                ADD COLUMN article_content TEXT
            """)
            print("✓ article_content 字段已添加")
        else:
            print("✓ article_content 字段已存在")

        # 提交更改
        conn.commit()

        # 验证
        cursor.execute("PRAGMA table_info(publish_history)")
        new_columns = [row[1] for row in cursor.fetchall()]
        print(f"\n更新后的字段: {new_columns}")

        cursor.close()
        conn.close()

        print("\n✓ 数据库迁移成功完成！")
        return True

    except Exception as e:
        print(f"\n✗ 数据库迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = migrate()
    sys.exit(0 if success else 1)
