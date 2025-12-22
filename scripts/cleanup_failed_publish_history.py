#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理发布历史脚本
删除状态为 'failed' 且没有文章标题的发布记录
"""
import sys
import os

# 添加backend目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_path = os.path.join(project_root, 'backend')
sys.path.insert(0, backend_path)

from models import PublishHistory, get_db_session
from sqlalchemy import or_


def cleanup_failed_publish_history(dry_run=True):
    """
    清理标题为"历史发布记录"的测试记录（不限制状态）

    Args:
        dry_run: 如果为True，只统计不删除；如果为False，执行删除
    """
    db = get_db_session()

    try:
        # 查询条件：article_title='历史发布记录'（不限制状态）
        query = db.query(PublishHistory).filter(
            PublishHistory.article_title == '历史发布记录'
        )

        # 统计数量
        count = query.count()

        print(f"\n{'='*60}")
        print(f"发布历史清理脚本")
        print(f"{'='*60}")
        print(f"模式: {'预览模式 (不会删除数据)' if dry_run else '删除模式 (会实际删除数据)'}")
        print(f"{'='*60}\n")

        if count == 0:
            print("[OK] 没有找到符合条件的记录")
            return 0

        print(f"找到 {count} 条符合条件的记录:\n")

        # 显示要删除的记录
        records = query.all()
        for i, record in enumerate(records[:20], 1):  # 最多显示前20条
            print(f"{i}. ID: {record.id}, 平台: {record.platform}, "
                  f"状态: {record.status}, 标题: {record.article_title or '(空)'}, "
                  f"发布时间: {record.published_at}")

        if count > 20:
            print(f"... 还有 {count - 20} 条记录未显示\n")
        else:
            print()

        if dry_run:
            print(f"[预览模式] 如果执行删除，将删除以上 {count} 条记录")
            print("\n提示: 使用 --execute 参数执行实际删除")
            return count
        else:
            # 确认删除
            confirm = input(f"\n[WARNING] 确认要删除这 {count} 条记录吗? (yes/no): ")
            if confirm.lower() != 'yes':
                print("[CANCEL] 取消删除操作")
                return 0

            # 执行删除
            deleted = query.delete(synchronize_session=False)
            db.commit()

            print(f"\n[OK] 成功删除 {deleted} 条记录")
            return deleted

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] 错误: {e}")
        import traceback
        traceback.print_exc()
        return -1
    finally:
        db.close()


if __name__ == '__main__':
    # 检查命令行参数
    execute = '--execute' in sys.argv or '-e' in sys.argv

    # 执行清理
    result = cleanup_failed_publish_history(dry_run=not execute)

    # 返回退出码
    sys.exit(0 if result >= 0 else 1)
