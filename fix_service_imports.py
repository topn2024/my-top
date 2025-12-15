#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量修复 service 文件中的 log_service_call 导入问题
"""

import os
import re

# 需要修复的文件列表
SERVICE_FILES = [
    'backend/services/account_service.py',
    'backend/services/ai_service.py',
    'backend/services/ai_service_v2.py',
    'backend/services/article_prompt_service.py',
    'backend/services/platform_style_service.py',
    'backend/services/prompt_combination_service.py',
    'backend/services/prompt_template_service.py',
]

# 要添加的导入代码
IMPORT_CODE = '''
try:
    from logger_config import log_service_call
except ImportError:
    # 如果没有 log_service_call，创建一个空装饰器
    def log_service_call(name):
        def decorator(func):
            return func
        return decorator
'''

def fix_file(filepath):
    """修复单个文件"""
    if not os.path.exists(filepath):
        print(f"跳过（文件不存在）: {filepath}")
        return False

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查是否已经有这个导入
    if 'from logger_config import log_service_call' in content or 'def log_service_call' in content:
        print(f"跳过（已有导入）: {filepath}")
        return False

    # 检查是否使用了 log_service_call
    if '@log_service_call' not in content:
        print(f"跳过（未使用）: {filepath}")
        return False

    # 找到合适的位置插入导入（在其他导入之后）
    lines = content.split('\n')
    insert_index = -1

    for i, line in enumerate(lines):
        # 找到最后一个 import 或 from 语句
        if line.strip().startswith(('import ', 'from ')):
            insert_index = i + 1

        # 如果找到了 class 定义，就在它之前插入
        if line.strip().startswith('class '):
            if insert_index == -1:
                insert_index = i
            break

    if insert_index == -1:
        print(f"错误（无法找到插入位置）: {filepath}")
        return False

    # 插入导入代码
    lines.insert(insert_index, IMPORT_CODE)

    # 写回文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"✓ 已修复: {filepath}")
    return True

def main():
    """主函数"""
    print("=" * 60)
    print("批量修复 service 文件导入问题")
    print("=" * 60)
    print()

    fixed_count = 0
    for filepath in SERVICE_FILES:
        if fix_file(filepath):
            fixed_count += 1

    print()
    print("=" * 60)
    print(f"修复完成！共修复 {fixed_count} 个文件")
    print("=" * 60)

if __name__ == '__main__':
    main()
