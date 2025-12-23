#!/usr/bin/env python3
"""
迁移发布历史数据：从旧系统(publish_history.db)到新系统(topn.db)
"""
import sys
import os
import sqlite3
from datetime import datetime

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from models import PublishHistory, Article, User, get_db_session
from sqlalchemy.orm import Session

def migrate_history():
    """迁移发布历史数据"""

    # 连接旧数据库
    old_db_path = os.path.join(os.path.dirname(__file__), 'backend', 'publish_history.db')
    print(f'连接旧数据库: {old_db_path}')
    old_conn = sqlite3.connect(old_db_path)
    old_conn.row_factory = sqlite3.Row
    old_cursor = old_conn.cursor()

    # 获取新数据库session
    new_db = get_db_session()

    try:
        # 获取admin用户（假设ID=1）
        admin_user = new_db.query(User).filter_by(username='admin').first()
        if not admin_user:
            print('错误: 未找到admin用户')
            return

        print(f'找到用户: {admin_user.username} (ID: {admin_user.id})')

        # 读取旧系统的所有记录
        old_cursor.execute('SELECT * FROM publish_history ORDER BY publish_time')
        old_records = old_cursor.fetchall()

        print(f'\n找到 {len(old_records)} 条旧记录')

        migrated = 0
        skipped = 0

        for record in old_records:
            # 检查是否已经迁移过（通过URL判断）
            existing = new_db.query(PublishHistory).filter_by(url=record['article_url']).first()
            if existing:
                print(f'跳过已存在记录: {record["title"][:30]}...')
                skipped += 1
                continue

            # 创建新记录
            new_record = PublishHistory(
                user_id=admin_user.id,
                article_id=None,  # 旧系统没有article_id关联
                platform=record['platform'] or '知乎',
                status=record['status'] or 'unknown',
                url=record['article_url'],
                message=record['error_message'] or ('发布成功' if record['status'] == 'success' else '发布失败'),
                published_at=datetime.strptime(record['publish_time'], '%Y-%m-%d %H:%M:%S') if record['publish_time'] else datetime.now()
            )

            new_db.add(new_record)
            migrated += 1
            print(f'迁移: {record["title"][:40]}... -> {record["status"]}')

        # 提交事务
        new_db.commit()

        print(f'\n✓ 迁移完成:')
        print(f'  成功迁移: {migrated} 条')
        print(f'  跳过重复: {skipped} 条')

        # 显示新系统统计
        total_new = new_db.query(PublishHistory).count()
        print(f'  新系统总记录: {total_new} 条')

    except Exception as e:
        print(f'\n✗ 迁移失败: {e}')
        new_db.rollback()
        raise
    finally:
        old_conn.close()
        new_db.close()

if __name__ == '__main__':
    print('='*60)
    print('发布历史数据迁移工具')
    print('='*60)
    migrate_history()
