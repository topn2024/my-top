#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据完整性检查脚本
检查所有数据库表的数据一致性、完整性和关联关系
"""
import sys
import io
from datetime import datetime
from sqlalchemy import text, inspect, and_, or_

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from models import (
    get_db_session,
    User, Article, PublishHistory, PublishTask,
    PlatformAccount, Workflow,
    PromptTemplate, PromptTemplateCategory, PromptTemplateAuditLog, PromptTemplateUsageLog,
    PromptExampleLibrary, PromptCombinationLog,
    AnalysisPrompt, ArticlePrompt, PlatformStylePrompt
)

def print_section(title):
    print('\n' + '=' * 80)
    print(title)
    print('=' * 80)

def print_subsection(title):
    print('\n' + '-' * 80)
    print(title)
    print('-' * 80)

def check_table_counts(db):
    """检查各表记录数"""
    print_section('数据库表统计')

    tables = {
        'users': User,
        'articles': Article,
        'publish_history': PublishHistory,
        'publish_tasks': PublishTask,
        'platform_accounts': PlatformAccount,
        'workflows': Workflow,
        'prompt_templates': PromptTemplate,
        'prompt_template_categories': PromptTemplateCategory,
        'prompt_template_audit_logs': PromptTemplateAuditLog,
        'prompt_template_usage_logs': PromptTemplateUsageLog,
        'prompt_example_library': PromptExampleLibrary,
        'prompt_combination_logs': PromptCombinationLog,
        'analysis_prompts': AnalysisPrompt,
        'article_prompts': ArticlePrompt,
        'platform_style_prompts': PlatformStylePrompt,
    }

    counts = {}
    for name, model in tables.items():
        count = db.query(model).count()
        counts[name] = count
        status = '✓' if count > 0 else '○'
        print(f'{status} {name}: {count} 条记录')

    return counts

def check_users(db):
    """检查用户表"""
    print_section('用户表 (users) 检查')

    users = db.query(User).all()
    print(f'总用户数: {len(users)}')

    issues = []

    for user in users:
        # 检查必填字段
        if not user.username:
            issues.append(f'用户 ID {user.id}: 缺少用户名')
        if not user.password:
            issues.append(f'用户 ID {user.id}: 缺少密码')

        # 检查关联数据
        article_count = db.query(Article).filter_by(user_id=user.id).count()
        publish_count = db.query(PublishHistory).filter_by(user_id=user.id).count()
        account_count = db.query(PlatformAccount).filter_by(user_id=user.id).count()

        print(f'用户: {user.username} (ID: {user.id})')
        print(f'  - 文章数: {article_count}')
        print(f'  - 发布历史: {publish_count}')
        print(f'  - 平台账号: {account_count}')
        print(f'  - 角色: {user.role}')
        print(f'  - 创建时间: {user.created_at}')

    if issues:
        print('\n⚠ 发现问题:')
        for issue in issues:
            print(f'  - {issue}')
    else:
        print('\n✓ 用户表数据完整')

def check_articles(db):
    """检查文章表"""
    print_section('文章表 (articles) 检查')

    articles = db.query(Article).all()
    print(f'总文章数: {len(articles)}')

    issues = []
    orphaned = []

    for article in articles:
        # 检查必填字段
        if not article.title:
            issues.append(f'文章 ID {article.id}: 缺少标题')
        if not article.content:
            issues.append(f'文章 ID {article.id}: 缺少内容')

        # 检查用户关联
        if article.user_id:
            user = db.query(User).filter_by(id=article.user_id).first()
            if not user:
                orphaned.append(f'文章 ID {article.id}: 关联用户 {article.user_id} 不存在')

        # 检查发布历史
        publish_count = db.query(PublishHistory).filter_by(article_id=article.id).count()

        print(f'文章 ID {article.id}: {article.title[:50] if article.title else "无标题"}...')
        print(f'  - 用户: {article.user.username if article.user else "未关联"}')
        print(f'  - 类型: {article.article_type}')
        print(f'  - 发布历史: {publish_count} 条')
        print(f'  - 内容长度: {len(article.content) if article.content else 0} 字符')
        print(f'  - 创建时间: {article.created_at}')

    if issues:
        print('\n⚠ 数据问题:')
        for issue in issues:
            print(f'  - {issue}')

    if orphaned:
        print('\n⚠ 孤立记录 (外键不存在):')
        for item in orphaned:
            print(f'  - {item}')

    if not issues and not orphaned:
        print('\n✓ 文章表数据完整')

def check_publish_history(db):
    """检查发布历史表"""
    print_section('发布历史表 (publish_history) 检查')

    histories = db.query(PublishHistory).all()
    print(f'总记录数: {len(histories)}')

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

    print(f'\n数据完整性:')
    print(f'  ✓ 有标题: {len(histories) - len(missing_title)} ({(len(histories) - len(missing_title)) * 100 // len(histories) if histories else 0}%)')
    print(f'  ✓ 有内容: {len(histories) - len(missing_content)} ({(len(histories) - len(missing_content)) * 100 // len(histories) if histories else 0}%)')
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
    tasks = db.query(PublishTask).filter(PublishTask.status == 'success').all()

    missing_in_history = []
    for task in tasks:
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
        print(f'  ⚠ publish_tasks 中有 {len(missing_in_history)} 条成功记录未在 publish_history 中')
    else:
        print(f'  ✓ 所有成功的任务都已记录在 publish_history 中')

def check_publish_tasks(db):
    """检查发布任务表"""
    print_section('发布任务表 (publish_tasks) 检查')

    tasks = db.query(PublishTask).all()
    print(f'总任务数: {len(tasks)}')

    status_stats = {}
    platform_stats = {}
    orphaned_users = []
    orphaned_articles = []

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

    print(f'\n状态分布:')
    for status, count in sorted(status_stats.items()):
        print(f'  - {status}: {count} 条')

    print(f'\n平台分布:')
    for platform, count in sorted(platform_stats.items()):
        print(f'  - {platform}: {count} 条')

    if orphaned_users:
        print(f'\n⚠ 孤立记录 (用户不存在): {len(orphaned_users)} 条')

    if orphaned_articles:
        print(f'\n⚠ 孤立记录 (文章不存在): {len(orphaned_articles)} 条')

def check_platform_accounts(db):
    """检查平台账号表"""
    print_section('平台账号表 (platform_accounts) 检查')

    accounts = db.query(PlatformAccount).all()
    print(f'总账号数: {len(accounts)}')

    issues = []
    orphaned = []
    platform_stats = {}

    for account in accounts:
        # 检查必填字段
        if not account.account_name:
            issues.append(f'账号 ID {account.id}: 缺少账号名称')
        if not account.cookies:
            issues.append(f'账号 ID {account.id}: 缺少cookies')

        # 检查用户关联
        if account.user_id:
            user = db.query(User).filter_by(id=account.user_id).first()
            if not user:
                orphaned.append(account.id)

        # 统计平台
        platform_stats[account.platform] = platform_stats.get(account.platform, 0) + 1

        print(f'账号: {account.account_name} (ID: {account.id})')
        print(f'  - 平台: {account.platform}')
        print(f'  - 所属用户: {account.user.username if account.user else "未关联"}')
        print(f'  - Cookies长度: {len(account.cookies) if account.cookies else 0}')
        print(f'  - 创建时间: {account.created_at}')

    print(f'\n平台分布:')
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

def check_workflows(db):
    """检查工作流表"""
    print_section('工作流表 (workflows) 检查')

    workflows = db.query(Workflow).all()
    print(f'总工作流数: {len(workflows)}')

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

        print(f'工作流 ID {wf.id}:')
        print(f'  - 所属用户: {wf.user.username if wf.user else "未关联"}')
        print(f'  - 状态: {wf.status}')
        print(f'  - 创建时间: {wf.created_at}')

    print(f'\n状态分布:')
    for status, count in sorted(status_stats.items()):
        print(f'  - {status}: {count} 条')

    if orphaned:
        print('\n⚠ 孤立记录 (用户不存在):')
        for wf_id in orphaned:
            print(f'  - 工作流 ID {wf_id}')

def check_prompt_templates(db):
    """检查提示词模板系统"""
    print_section('提示词模板系统检查')

    templates = db.query(PromptTemplate).all()
    categories = db.query(PromptTemplateCategory).all()
    audit_logs = db.query(PromptTemplateAuditLog).all()
    usage_logs = db.query(PromptTemplateUsageLog).all()

    print(f'模板总数: {len(templates)}')
    print(f'分类总数: {len(categories)}')
    print(f'审计日志: {len(audit_logs)} 条')
    print(f'使用日志: {len(usage_logs)} 条')

    # 检查模板与分类的关联
    orphaned_templates = []
    for template in templates:
        if template.category_id:
            category = db.query(PromptTemplateCategory).filter_by(id=template.category_id).first()
            if not category:
                orphaned_templates.append(template.id)

    if orphaned_templates:
        print(f'\n⚠ 孤立模板 (分类不存在): {len(orphaned_templates)} 个')
    else:
        print('\n✓ 所有模板的分类关联都有效')

    # 检查分类层级
    print(f'\n分类层级结构:')
    root_categories = [c for c in categories if not c.parent_id]
    print(f'  - 根分类: {len(root_categories)} 个')

    for root in root_categories:
        children = [c for c in categories if c.parent_id == root.id]
        print(f'    {root.name} (ID: {root.id}): {len(children)} 个子分类')

def main():
    """主函数"""
    print('=' * 80)
    print('数据库完整性检查报告')
    print('=' * 80)
    print(f'检查时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

    db = get_db_session()

    try:
        # 执行各项检查
        check_table_counts(db)
        check_users(db)
        check_articles(db)
        check_publish_history(db)
        check_publish_tasks(db)
        check_platform_accounts(db)
        check_workflows(db)
        check_prompt_templates(db)

        # 总结
        print_section('检查总结')
        print('✓ 数据完整性检查已完成')
        print('\n建议:')
        print('  1. 处理所有标记为 ⚠ 的问题')
        print('  2. 清理孤立记录 (外键关联不存在的记录)')
        print('  3. 补充缺失的必填字段')
        print('  4. 确保 publish_history 和 publish_tasks 的数据一致性')

    except Exception as e:
        print(f'\n✗ 检查失败: {e}')
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    main()
