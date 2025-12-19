#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据整合迁移脚本：
将 publish_tasks 和 articles 表的数据整合到 publish_history 表中
确保 article_title 和 article_content 字段完整
"""
import sys
import io
from datetime import datetime

# 设置标准输出为UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from models import get_db_session, PublishHistory, PublishTask, Article
from sqlalchemy import and_, or_

def migrate_data():
    """执行数据整合迁移"""

    print('=' * 80)
    print('发布历史数据整合迁移')
    print('=' * 80)
    print(f'开始时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print()

    db = get_db_session()

    try:
        # ============ 第1步：统计当前数据 ============
        print('第1步：统计当前数据')
        print('-' * 80)

        total_history = db.query(PublishHistory).count()
        total_tasks = db.query(PublishTask).count()
        total_articles = db.query(Article).count()

        print(f'publish_history 表：{total_history} 条记录')
        print(f'publish_tasks 表：{total_tasks} 条记录')
        print(f'articles 表：{total_articles} 条记录')

        # 统计 publish_history 中缺少标题/内容的记录
        missing_title = db.query(PublishHistory).filter(
            or_(
                PublishHistory.article_title == None,
                PublishHistory.article_title == ''
            )
        ).count()

        missing_content = db.query(PublishHistory).filter(
            or_(
                PublishHistory.article_content == None,
                PublishHistory.article_content == ''
            )
        ).count()

        print(f'publish_history 中缺少标题的记录：{missing_title} 条')
        print(f'publish_history 中缺少内容的记录：{missing_content} 条')
        print()

        # ============ 第2步：从 publish_tasks 补充数据 ============
        print('第2步：从 publish_tasks 表补充数据')
        print('-' * 80)

        updated_from_tasks = 0

        # 查找所有缺少标题或内容的 publish_history 记录
        history_records = db.query(PublishHistory).filter(
            or_(
                PublishHistory.article_title == None,
                PublishHistory.article_title == '',
                PublishHistory.article_content == None,
                PublishHistory.article_content == ''
            )
        ).all()

        print(f'找到 {len(history_records)} 条需要补充的记录')

        for history in history_records:
            # 尝试通过 URL 匹配 publish_tasks
            if history.url:
                task = db.query(PublishTask).filter(
                    PublishTask.user_id == history.user_id,
                    PublishTask.result_url == history.url
                ).first()

                if task:
                    updated = False

                    # 补充标题
                    if not history.article_title and task.article_title:
                        history.article_title = task.article_title
                        updated = True

                    # 补充内容
                    if not history.article_content and task.article_content:
                        history.article_content = task.article_content
                        updated = True

                    if updated:
                        updated_from_tasks += 1
                        print(f'  [URL匹配] 记录 #{history.id} 从 task #{task.id} 补充数据')

            # 尝试通过 article_id 匹配 publish_tasks
            elif history.article_id:
                task = db.query(PublishTask).filter(
                    PublishTask.user_id == history.user_id,
                    PublishTask.article_id == history.article_id,
                    PublishTask.status == 'success'
                ).first()

                if task:
                    updated = False

                    if not history.article_title and task.article_title:
                        history.article_title = task.article_title
                        updated = True

                    if not history.article_content and task.article_content:
                        history.article_content = task.article_content
                        updated = True

                    if updated:
                        updated_from_tasks += 1
                        print(f'  [文章ID匹配] 记录 #{history.id} 从 task #{task.id} 补充数据')

        print(f'从 publish_tasks 补充：{updated_from_tasks} 条记录')
        print()

        # ============ 第3步：从 articles 表补充数据 ============
        print('第3步：从 articles 表补充数据')
        print('-' * 80)

        updated_from_articles = 0

        # 查找有 article_id 但缺少标题/内容的记录
        history_with_article = db.query(PublishHistory).filter(
            PublishHistory.article_id != None,
            or_(
                PublishHistory.article_title == None,
                PublishHistory.article_title == '',
                PublishHistory.article_content == None,
                PublishHistory.article_content == ''
            )
        ).all()

        print(f'找到 {len(history_with_article)} 条有 article_id 但缺少数据的记录')

        for history in history_with_article:
            article = db.query(Article).filter(Article.id == history.article_id).first()

            if article:
                updated = False

                # 补充标题
                if not history.article_title and article.title:
                    history.article_title = article.title
                    updated = True

                # 补充内容
                if not history.article_content and article.content:
                    history.article_content = article.content
                    updated = True

                if updated:
                    updated_from_articles += 1
                    print(f'  记录 #{history.id} 从 article #{article.id} 补充数据')

        print(f'从 articles 补充：{updated_from_articles} 条记录')
        print()

        # ============ 第4步：从 publish_tasks 创建缺失的 publish_history 记录 ============
        print('第4步：从 publish_tasks 创建缺失的 publish_history 记录')
        print('-' * 80)

        created_from_tasks = 0

        # 查找所有成功的 publish_tasks，但没有对应的 publish_history
        success_tasks = db.query(PublishTask).filter(
            PublishTask.status == 'success',
            PublishTask.result_url != None
        ).all()

        print(f'找到 {len(success_tasks)} 条成功的任务记录')

        for task in success_tasks:
            # 检查是否已存在对应的 publish_history 记录
            existing = db.query(PublishHistory).filter(
                and_(
                    PublishHistory.user_id == task.user_id,
                    PublishHistory.url == task.result_url
                )
            ).first()

            if not existing:
                # 创建新的 publish_history 记录
                new_history = PublishHistory(
                    user_id=task.user_id,
                    article_id=task.article_id,
                    article_title=task.article_title,
                    article_content=task.article_content,
                    platform=task.platform,
                    status='success',
                    url=task.result_url,
                    message=task.error_message or '从任务记录迁移',
                    published_at=task.updated_at or task.created_at
                )
                db.add(new_history)
                created_from_tasks += 1
                print(f'  创建新记录：task #{task.id} -> 标题: {task.article_title[:30] if task.article_title else "无"}...')

        print(f'从 publish_tasks 创建新记录：{created_from_tasks} 条')
        print()

        # ============ 第5步：提交更改 ============
        print('第5步：提交更改到数据库')
        print('-' * 80)

        db.commit()
        print('✓ 数据已成功提交')
        print()

        # ============ 第6步：验证结果 ============
        print('第6步：验证迁移结果')
        print('-' * 80)

        final_total = db.query(PublishHistory).count()
        final_missing_title = db.query(PublishHistory).filter(
            or_(
                PublishHistory.article_title == None,
                PublishHistory.article_title == ''
            )
        ).count()

        final_missing_content = db.query(PublishHistory).filter(
            or_(
                PublishHistory.article_content == None,
                PublishHistory.article_content == ''
            )
        ).count()

        print(f'迁移后统计：')
        print(f'  总记录数：{total_history} -> {final_total} (增加 {final_total - total_history})')
        print(f'  缺少标题：{missing_title} -> {final_missing_title} (减少 {missing_title - final_missing_title})')
        print(f'  缺少内容：{missing_content} -> {final_missing_content} (减少 {missing_content - final_missing_content})')
        print()

        # ============ 总结 ============
        print('=' * 80)
        print('迁移总结')
        print('=' * 80)
        print(f'✓ 从 publish_tasks 补充数据：{updated_from_tasks} 条')
        print(f'✓ 从 articles 补充数据：{updated_from_articles} 条')
        print(f'✓ 从 publish_tasks 创建新记录：{created_from_tasks} 条')
        print(f'✓ 总计处理：{updated_from_tasks + updated_from_articles + created_from_tasks} 条')
        print()
        print(f'完成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        print('=' * 80)

        return True

    except Exception as e:
        print(f'\n✗ 迁移失败: {e}')
        import traceback
        traceback.print_exc()
        db.rollback()
        return False

    finally:
        db.close()

if __name__ == '__main__':
    print('\n' + '!' * 80)
    print('警告：此脚本将修改数据库数据')
    print('建议先备份数据库：cp data/topn.db data/topn.db.backup')
    print('!' * 80)
    print()

    response = input('确定要继续吗？(yes/no): ')

    if response.lower() in ['yes', 'y']:
        success = migrate_data()
        sys.exit(0 if success else 1)
    else:
        print('操作已取消')
        sys.exit(0)
