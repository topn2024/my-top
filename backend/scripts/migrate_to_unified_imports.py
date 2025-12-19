"""
自动迁移所有导入从 models.py 到 models_unified.py
"""
import os
import re
import sys

# 需要迁移的文件列表（排除测试文件和迁移脚本本身）
FILES_TO_MIGRATE = [
    # 主应用
    'app_with_upload.py',
    'auth.py',
    'auth_decorators.py',
    'database.py',

    # Blueprints
    'blueprints/api.py',
    'blueprints/api_retry.py',
    'blueprints/prompt_template_api.py',

    # Services
    'services/account_service.py',
    'services/analysis_prompt_service.py',
    'services/article_prompt_service.py',
    'services/platform_style_service.py',
    'services/prompt_combination_service.py',
    'services/prompt_template_service.py',
    'services/publish_service.py',
    'services/publish_worker.py',
    'services/task_queue_manager.py',
    'services/workflow_service.py',

    # 其他核心文件
    'rbac_permissions.py',
    'csdn_wechat_login.py',
]

def migrate_file(filepath):
    """迁移单个文件的导入"""
    if not os.path.exists(filepath):
        print(f"⚠️  文件不存在: {filepath}")
        return False

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # 替换导入语句
    content = re.sub(
        r'from models import',
        'from models_unified import',
        content
    )

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ 已迁移: {filepath}")
        return True
    else:
        print(f"ℹ️  无需迁移: {filepath}")
        return False

def main():
    print("=" * 60)
    print("  开始迁移导入语句: models.py → models_unified.py")
    print("=" * 60)
    print()

    migrated_count = 0
    failed_count = 0

    for filepath in FILES_TO_MIGRATE:
        full_path = filepath
        try:
            if migrate_file(full_path):
                migrated_count += 1
        except Exception as e:
            print(f"❌ 迁移失败 {filepath}: {str(e)}")
            failed_count += 1

    print()
    print("=" * 60)
    print("  迁移完成")
    print("=" * 60)
    print(f"✅ 成功迁移: {migrated_count} 个文件")
    print(f"❌ 失败: {failed_count} 个文件")
    print()

    if migrated_count > 0:
        print("⚠️  重要提示:")
        print("1. 请运行测试验证迁移结果")
        print("2. 检查应用是否正常启动")
        print("3. 验证数据库连接")
        print()

if __name__ == '__main__':
    main()
