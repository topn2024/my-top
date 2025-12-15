#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加template_id列到workflows表
"""
from sqlalchemy import text
from models import SessionLocal

def add_template_id_column():
    """添加template_id列到workflows表"""
    session = SessionLocal()
    try:
        # 检查template_id列是否已存在
        result = session.execute(text("PRAGMA table_info(workflows)"))
        columns = [row[1] for row in result]

        if 'template_id' in columns:
            print('[OK] template_id column already exists')
        else:
            print('[INFO] Adding template_id column to workflows table...')
            session.execute(text("ALTER TABLE workflows ADD COLUMN template_id VARCHAR(100)"))
            session.commit()
            print('[OK] template_id column added successfully')

    except Exception as e:
        session.rollback()
        print(f'[ERROR] {str(e)}')
        raise
    finally:
        session.close()

if __name__ == '__main__':
    print('Starting migration...')
    add_template_id_column()
    print('[OK] Migration completed')
