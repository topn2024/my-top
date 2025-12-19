#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据完整性检查脚本（简化版）
检查核心表的数据一致性、完整性和关联关系
"""
import sys
import io
from datetime import datetime
from sqlalchemy import text, inspect, and_, or_

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from models import (
    get_db_session,
    User, Article, PublishHistory, PublishTask, PlatformAccount, Workflow
)

def print_section(title):
    print('\n' + '=' * 80)
    print(title)
    print('=' * 80)

def check_all_tables(db):
    """检查所有表的记录数"""
    print_section('数据库表统计')

    inspector = inspect(db.bind)
    tables = inspector.get_table_names()

    print(f'数据库共有 {len(tables)} 个表:\n')

    for table in tables:
        try:
            result = db.execute(text(f'SELECT COUNT(*) FROM {table}'))
            count = result.scalar()
            status = '✓' if count > 0 else '○'
            print(f'{status} {table}: {count} 条记录')
        except Exception as e:
            print(f'✗ {table}: 查询失败')

def check_users(db):
    """检查用户表"""
    print_section('用户表 (users) 详细检查')

    users = db.query(User).all()
    print(f'总用户数: {len(users)}\n')

    issues = []

    for user in users:
        # 检查必填字段
        if not user.username:
            issues.append(f'用户 ID {user.id}: 缺少用户名')
        if not user.password_hash:
            issues.append(f'用户 ID {user.id}: 缺少密码')

        # 检查关联数据
        workflow_count = db.query(Workflow).filter_by(user_id=user.id).count()
        publish_count = db.query(PublishHistory).filter_by(user_id=user.id).count()
        account_count = db.query(PlatformAccount).filter_by(user_id=user.id).count()

        # 通过workflows获取文章数
        article_count = 0
        for workflow in db.query(Workflow).filter_by(user_id=user.id).all():
            article_count += db.query(Article).filter_by(workflow_id=workflow.id).count()

        print(f'用户: {user.username} (ID: {user.id}, 角色: {user.role})')
        print(f'  - 工作流: {workflow_count}')
        print(f'  - 文章数: {article_count} (通过工作流)')
        print(f'  - 发布历史: {publish_count}')
        print(f'  - 平台账号: {account_count}')
        print(f'  - 创建时间: {user.created_at}')
        print()

    if issues:
        print('⚠ 发现问题:')
        for issue in issues:
            print(f'  - {issue}')
    else:
        print('✓ 用户表数据完整')

def check_articles(db):
    """检查文章表"""
    print_section('文章表 (articles) 详细检查')

    articles = db.query(Article).all()
    print(f'总文章数: {len(articles)}\n')

    issues = []
    orphaned = []

    for article in articles:
        # 检查必填字段
        if not article.title:
            issues.append(f'文章 ID {article.id}: 缺少标题')
        if not article.content:
            issues.append(f'文章 ID {article.id}: 缺少内容')

        # 检查workflow关联
        if article.workflow_id:
            workflow = db.query(Workflow).filter_by(id=article.workflow_id).first()
            if not workflow:
                orphaned.append(f'文章 ID {article.id}: 关联工作流 {article.workflow_id} 不存在')
        else:
            orphaned.append(f'文章 ID {article.id}: 没有关联工作流')

        # 检查发布历史
        publish_count = db.query(PublishHistory).filter_by(article_id=article.id).count()

        title_display = article.title[:40] if article.title else "无标题"
        print(f'文章 ID {article.id}: {title_display}...')

        # 获取用户信息（通过workflow）
        user_name = "未关联"
        if article.workflow:
            user_name = article.workflow.user.username if article.workflow.user else "未关联"

        print(f'  - 用户: {user_name} (通过工作流 ID {article.workflow_id})')
        print(f'  - 类型: {article.article_type}')
        print(f'  - 发布历史: {publish_count} 条')
        print(f'  - 内容长度: {len(article.content) if article.content else 0} 字符')
        print(f'  - 创建时间: {article.created_at}')
        print()

    if issues:
        print('⚠ 数据问题:')
        for issue in issues:
            print(f'  - {issue}')

    if orphaned:
        print('\n⚠ 孤立记录 (外键不存在):')
        for item in orphaned:
            print(f'  - {item}')

    if not issues and not orphaned:
        print('✓ 文章表数据完整')

def check_publish_history(db):
    """检查发布历史表"""
    print_section('发布历史表 (publish_history) 详细检查')

    histories = db.query(PublishHistory).all()
    print(f'总记录数: {len(histories)}\n')

    # 统计数据完整性
    missing_title = []
    missing_content = []
    orphaned_users = []
    orphaned_articles = []
    platform_stats = {}
    status_stats = {}

    for h in histories:
        # 检查标题
        if not h.article_title or not h.article_title.strip():
            missing_title.append(h.id)

        # 检查内容
        if not h.article_content or not h.article_content.strip():
            missing_content.append(h.id)

        # 检查用户关联
        if h.user_id:
            user = db.query(User).filter_by(id=h.user_id).first()
            if not user:
                orphaned_users.append(h.id)

        # 检查文章关联
        if h.article_id:
            article = db.query(Article).filter_by(id=h.article_id).first()
            if not article:
                orphaned_articles.append(h.id)

        # 统计平台
        platform_stats[h.platform] = platform_stats.get(h.platform, 0) + 1

        # 统计状态
        status_stats[h.status] = status_stats.get(h.status, 0) + 1

    print('数据完整性:')
    total = len(histories)
    if total > 0:
        print(f'  ✓ 有标题: {total - len(missing_title)} ({(total - len(missing_title)) * 100 // total}%)')
        print(f'  ✓ 有内容: {total - len(missing_content)} ({(total - len(missing_content)) * 100 // total}%)')
        print(f'  ⚠ 缺少标题: {len(missing_title)} 条')
        print(f'  ⚠ 缺少内容: {len(missing_content)} 条')

    print(f'\n平台分布:')
    for platform, count in sorted(platform_stats.items()):
        print(f'  - {platform}: {count} 条')

    print(f'\n状态分布:')
    for status, count in sorted(status_stats.items()):
        print(f'  - {status}: {count} 条')

    if orphaned_users:
        print(f'\n⚠ 孤立记录 (用户不存在): {len(orphaned_users)} 条')
        print(f'  记录ID: {orphaned_users[:10]}{"..." if len(orphaned_users) > 10 else ""}')

    if orphaned_articles:
        print(f'\n⚠ 孤立记录 (文章不存在): {len(orphaned_articles)} 条')
        print(f'  记录ID: {orphaned_articles[:10]}{"..." if len(orphaned_articles) > 10 else ""}')

    # 检查与 publish_tasks 的一致性
    print(f'\n与 publish_tasks 表的一致性:')
    success_tasks = db.query(PublishTask).filter(PublishTask.status == 'success').all()
    failed_tasks = db.query(PublishTask).filter(PublishTask.status == 'failed').all()

    print(f'  - publish_tasks 成功任务: {len(success_tasks)} 条')
    print(f'  - publish_tasks 失败任务: {len(failed_tasks)} 条')

    missing_in_history = []
    for task in success_tasks:
        if task.result_url:
            history = db.query(PublishHistory).filter(
                and_(
                    PublishHistory.user_id == task.user_id,
                    PublishHistory.url == task.result_url
                )
            ).first()
            if not history:
                missing_in_history.append(task.id)

    if missing_in_history:
        print(f'  ⚠ {len(missing_in_history)} 条成功任务未在 publish_history 中')
    else:
        print(f'  ✓ 所有成功任务都已记录')

    # 显示缺少内容的记录详情
    if missing_content:
        print(f'\n缺少内容的记录详情 (前5条):')
        for record_id in missing_content[:5]:
            h = db.query(PublishHistory).filter_by(id=record_id).first()
            if h:
                print(f'  ID {h.id}: {h.article_title[:40] if h.article_title else "无标题"}...')
                print(f'    平台: {h.platform}, 状态: {h.status}, URL: {h.url if h.url else "无"}')

def check_publish_tasks(db):
    """检查发布任务表"""
    print_section('发布任务表 (publish_tasks) 详细检查')

    tasks = db.query(PublishTask).all()
    print(f'总任务数: {len(tasks)}\n')

    status_stats = {}
    platform_stats = {}
    orphaned_users = []
    orphaned_articles = []
    missing_data = []

    for task in tasks:
        # 统计状态
        status_stats[task.status] = status_stats.get(task.status, 0) + 1

        # 统计平台
        platform_stats[task.platform] = platform_stats.get(task.platform, 0) + 1

        # 检查用户关联
        if task.user_id:
            user = db.query(User).filter_by(id=task.user_id).first()
            if not user:
                orphaned_users.append(task.id)

        # 检查文章关联
        if task.article_id:
            article = db.query(Article).filter_by(id=task.article_id).first()
            if not article:
                orphaned_articles.append(task.id)

        # 检查数据完整性
        if not task.article_title or not task.article_content:
            missing_data.append(task.id)

    print('状态分布:')
    for status, count in sorted(status_stats.items()):
        print(f'  - {status}: {count} 条')

    print(f'\n平台分布:')
    for platform, count in sorted(platform_stats.items()):
        print(f'  - {platform}: {count} 条')

    print(f'\n数据完整性:')
    print(f'  ✓ 有完整数据 (标题+内容): {len(tasks) - len(missing_data)} 条')
    print(f'  ⚠ 数据不完整: {len(missing_data)} 条')

    if orphaned_users:
        print(f'\n⚠ 孤立记录 (用户不存在): {len(orphaned_users)} 条')

    if orphaned_articles:
        print(f'\n⚠ 孤立记录 (文章不存在): {len(orphaned_articles)} 条')

    # 显示任务详情
    print(f'\n任务详情:')
    for task in tasks[:5]:
        title = task.article_title[:30] if task.article_title else "无标题"
        print(f'  ID {task.id}: {title}...')
        print(f'    状态: {task.status}, 平台: {task.platform}')
        print(f'    URL: {task.result_url if task.result_url else "无"}')
        print(f'    内容长度: {len(task.article_content) if task.article_content else 0} 字符')
        print()

def check_platform_accounts(db):
    """检查平台账号表"""
    print_section('平台账号表 (platform_accounts) 详细检查')

    accounts = db.query(PlatformAccount).all()
    print(f'总账号数: {len(accounts)}\n')

    issues = []
    orphaned = []
    platform_stats = {}

    for account in accounts:
        # 检查必填字段
        if not account.username:
            issues.append(f'账号 ID {account.id}: 缺少用户名')
        if not account.password_encrypted:
            issues.append(f'账号 ID {account.id}: 缺少密码')

        # 检查用户关联
        if account.user_id:
            user = db.query(User).filter_by(id=account.user_id).first()
            if not user:
                orphaned.append(account.id)

        # 统计平台
        platform_stats[account.platform] = platform_stats.get(account.platform, 0) + 1

        print(f'账号: {account.username} @ {account.platform} (ID: {account.id})')
        print(f'  - 所属用户: {account.user.username if account.user else "未关联"}')
        print(f'  - 状态: {account.status}')
        print(f'  - 创建时间: {account.created_at}')
        if account.last_tested:
            print(f'  - 最后测试: {account.last_tested}')
        print()

    print('平台分布:')
    for platform, count in sorted(platform_stats.items()):
        print(f'  - {platform}: {count} 个账号')

    if issues:
        print('\n⚠ 数据问题:')
        for issue in issues:
            print(f'  - {issue}')

    if orphaned:
        print('\n⚠ 孤立记录 (用户不存在):')
        for account_id in orphaned:
            print(f'  - 账号 ID {account_id}')

    if not issues and not orphaned:
        print('\n✓ 平台账号表数据完整')

def check_workflows(db):
    """检查工作流表"""
    print_section('工作流表 (workflows) 详细检查')

    workflows = db.query(Workflow).all()
    print(f'总工作流数: {len(workflows)}\n')

    orphaned = []
    status_stats = {}

    for wf in workflows:
        # 检查用户关联
        if wf.user_id:
            user = db.query(User).filter_by(id=wf.user_id).first()
            if not user:
                orphaned.append(wf.id)

        # 统计状态
        status_stats[wf.status] = status_stats.get(wf.status, 0) + 1

    print('工作流列表:')
    for wf in workflows[:10]:
        print(f'  ID {wf.id}: 用户 {wf.user.username if wf.user else "未关联"}, 状态: {wf.status}')

    print(f'\n状态分布:')
    for status, count in sorted(status_stats.items()):
        print(f'  - {status}: {count} 条')

    if orphaned:
        print('\n⚠ 孤立记录 (用户不存在):')
        for wf_id in orphaned:
            print(f'  - 工作流 ID {wf_id}')
    else:
        print('\n✓ 工作流表数据完整')

def generate_summary(db):
    """生成检查总结"""
    print_section('数据完整性检查总结')

    issues = []

    # 检查用户
    users = db.query(User).all()
    for user in users:
        if not user.username or not user.password_hash:
            issues.append(f'用户 ID {user.id} 缺少必填字段')

    # 检查文章
    articles = db.query(Article).all()
    orphaned_articles = 0
    for article in articles:
        if article.workflow_id:
            workflow = db.query(Workflow).filter_by(id=article.workflow_id).first()
            if not workflow:
                orphaned_articles += 1

    # 检查发布历史
    histories = db.query(PublishHistory).all()
    missing_content = sum(1 for h in histories if not h.article_content or not h.article_content.strip())

    # 输出总结
    print(f'检查完成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print()
    print('发现的问题:')

    if missing_content > 0:
        issues.append(f'publish_history 表有 {missing_content} 条记录缺少内容')

    if orphaned_articles > 0:
        issues.append(f'articles 表有 {orphaned_articles} 条孤立记录 (工作流不存在)')

    if issues:
        for i, issue in enumerate(issues, 1):
            print(f'  {i}. {issue}')
    else:
        print('  ✓ 未发现严重问题')

    print()
    print('建议:')
    if missing_content > 0:
        print(f'  1. 为 {missing_content} 条发布历史补充内容数据')
    if orphaned_articles > 0:
        print(f'  2. 清理或修复 {orphaned_articles} 条孤立的文章记录')
    if not issues:
        print('  - 数据状态良好，继续保持')

def main():
    """主函数"""
    print('=' * 80)
    print('数据库完整性检查报告')
    print('=' * 80)
    print(f'检查时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

    db = get_db_session()

    try:
        # 执行各项检查
        check_all_tables(db)
        check_users(db)
        check_articles(db)
        check_publish_history(db)
        check_publish_tasks(db)
        check_platform_accounts(db)
        check_workflows(db)
        generate_summary(db)

    except Exception as e:
        print(f'\n✗ 检查失败: {e}')
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    main()
