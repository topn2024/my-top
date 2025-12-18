#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迁移到统一模型文件
- 这个脚本帮助从分散的模型文件迁移到统一的 models_unified.py
- 确保数据完整性和向后兼容性
"""
import sys
import os
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import shutil
from datetime import datetime


def backup_current_models():
    """备份当前的模型文件"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = Path(__file__).parent / f'model_backup_{timestamp}'
    backup_dir.mkdir(exist_ok=True)

    files_to_backup = [
        'models.py',
        'models_prompt_template.py',
        'models_prompt_v2.py'
    ]

    print(f"📦 备份当前模型文件到: {backup_dir}")

    for file in files_to_backup:
        src = Path(__file__).parent.parent / file
        if src.exists():
            dst = backup_dir / file
            shutil.copy2(src, dst)
            print(f"  ✓ 备份: {file}")

    return backup_dir


def create_migration_log(backup_dir):
    """创建迁移日志"""
    log_file = backup_dir / 'migration_log.txt'

    log_content = f"""
# 模型文件迁移日志

## 迁移时间
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 迁移说明
将以下文件整合为统一的 models_unified.py:
- backend/models.py (核心业务模型)
- backend/models_prompt_v2.py (提示词系统模型)

## 备份位置
{backup_dir.absolute()}

## 迁移步骤
1. ✓ 备份现有模型文件
2. ✓ 创建统一模型文件 (models_unified.py)
3. [ ] 替换 models.py 为新文件
4. [ ] 更新所有导入引用
5. [ ] 测试验证
6. [ ] 清理废弃文件

## 向后兼容性
models_unified.py 包含所有现有模型的定义，确保:
- 表名完全一致
- 字段定义完全一致
- 关系定义完全一致
- 数据不会丢失

## 回滚方法
如果出现问题，可以从备份目录恢复:
```bash
cp {backup_dir}/models.py backend/
```

## 后续清理
迁移成功后，可以安全删除:
- backend/models_prompt_template.py
- backend/models_prompt_v2.py
"""

    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(log_content)

    print(f"📝 创建迁移日志: {log_file}")


def replace_models_file():
    """将 models.py 替换为统一版本"""
    backend_dir = Path(__file__).parent.parent
    old_model = backend_dir / 'models.py'
    new_model = backend_dir / 'models_unified.py'

    if not new_model.exists():
        print("❌ 错误: models_unified.py 不存在")
        return False

    # 创建一个临时备份
    temp_backup = backend_dir / f'models.py.pre_migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    if old_model.exists():
        shutil.copy2(old_model, temp_backup)
        print(f"🔒 创建临时备份: {temp_backup.name}")

    try:
        # 替换文件
        shutil.copy2(new_model, old_model)
        print("✓ models.py 已更新为统一版本")
        return True
    except Exception as e:
        print(f"❌ 替换失败: {e}")
        # 恢复备份
        if temp_backup.exists():
            shutil.copy2(temp_backup, old_model)
            print("↩️  已从备份恢复")
        return False


def find_and_list_imports():
    """查找所有导入旧模型的文件"""
    backend_dir = Path(__file__).parent.parent
    project_root = backend_dir.parent

    import_patterns = [
        'from models_prompt_v2 import',
        'from models_prompt_template import',
        'import models_prompt_v2',
        'import models_prompt_template'
    ]

    files_to_update = []

    # 搜索 Python 文件
    for py_file in project_root.rglob('*.py'):
        # 跳过备份和迁移文件
        if 'backup' in str(py_file) or 'migration' in str(py_file):
            continue

        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()

            for pattern in import_patterns:
                if pattern in content:
                    files_to_update.append(py_file)
                    break
        except Exception:
            continue

    if files_to_update:
        print("\n📋 需要更新导入的文件:")
        for file in files_to_update:
            rel_path = file.relative_to(project_root)
            print(f"  - {rel_path}")
    else:
        print("\n✓ 没有发现需要更新的导入")

    return files_to_update


def update_imports():
    """更新所有文件中的导入语句"""
    files = find_and_list_imports()

    if not files:
        return True

    print("\n⚠️  请手动检查并更新以上文件中的导入语句")
    print("   将 'from models_prompt_v2 import' 改为 'from models import'")

    return False


def verify_database():
    """验证数据库结构"""
    try:
        # 导入新模型
        from models_unified import engine, Base
        from sqlalchemy import inspect

        inspector = inspect(engine)
        tables = inspector.get_table_names()

        print("\n🔍 当前数据库表:")
        expected_tables = [
            'users', 'workflows', 'articles', 'platform_accounts',
            'publish_history', 'publish_tasks',
            'analysis_prompts', 'article_prompts',
            'platform_style_prompts', 'prompt_combination_logs'
        ]

        for table in expected_tables:
            if table in tables:
                print(f"  ✓ {table}")
            else:
                print(f"  ✗ {table} (缺失)")

        return True
    except Exception as e:
        print(f"❌ 数据库验证失败: {e}")
        return False


def main():
    """主迁移流程"""
    print("="* 60)
    print("  模型文件迁移工具")
    print("="* 60)

    # 1. 备份
    print("\n步骤 1/5: 备份当前模型文件")
    backup_dir = backup_current_models()
    create_migration_log(backup_dir)

    # 2. 检查统一模型文件
    print("\n步骤 2/5: 检查统一模型文件")
    unified_model = Path(__file__).parent.parent / 'models_unified.py'
    if not unified_model.exists():
        print("❌ models_unified.py 不存在,请先创建")
        return

    print("✓ models_unified.py 已就绪")

    # 3. 询问是否继续
    print("\n步骤 3/5: 准备替换 models.py")
    response = input("是否继续替换 models.py? (yes/no): ")

    if response.lower() != 'yes':
        print("⏸️  迁移已取消")
        return

    # 4. 替换文件
    if not replace_models_file():
        print("\n❌ 迁移失败")
        return

    # 5. 检查导入
    print("\n步骤 4/5: 检查导入语句")
    find_and_list_imports()

    # 6. 验证数据库
    print("\n步骤 5/5: 验证数据库结构")
    verify_database()

    # 完成
    print("\n" + "="* 60)
    print("  ✓ 迁移完成!")
    print("="* 60)
    print(f"\n备份位置: {backup_dir.absolute()}")
    print("\n后续步骤:")
    print("1. 测试应用是否正常运行")
    print("2. 检查所有功能")
    print("3. 如果一切正常,可以删除废弃文件:")
    print("   - backend/models_prompt_template.py")
    print("   - backend/models_prompt_v2.py")
    print("   - backend/models.py.pre_migration_*")


if __name__ == '__main__':
    main()
