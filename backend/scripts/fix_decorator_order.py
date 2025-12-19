#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复装饰器顺序问题
@log_service_call 应该在 @staticmethod/@classmethod 之后
"""
import os
import re

def fix_decorator_order(filepath):
    """修复单个文件的装饰器顺序"""
    print(f"\nChecking: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # 查找错误的装饰器顺序模式
    # 匹配: @log_service_call("...")\n@staticmethod 或 @log_service_call("...")\n@classmethod
    pattern = r'(\s+)@log_service_call\("([^"]+)"\)\s*\n@(staticmethod|classmethod)\s*\n(\s+)def\s+(\w+)'

    def replace_func(match):
        indent = match.group(1)
        description = match.group(2)
        decorator_type = match.group(3)
        func_indent = match.group(4)
        func_name = match.group(5)

        print(f"  Fixing: {func_name} - {description}")

        # 正确的顺序: @staticmethod/@classmethod 在前, @log_service_call 在后
        return f'{indent}@{decorator_type}\n{indent}@log_service_call("{description}")\n{func_indent}def {func_name}'

    content = re.sub(pattern, replace_func, content)

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  [FIXED] File updated")
        return True
    else:
        print(f"  [OK] No issues found")
        return False

def main():
    """主函数"""
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    services_dir = os.path.join(backend_dir, 'services')

    # 需要检查的文件
    files_to_check = [
        'analysis_prompt_service.py',
        'article_prompt_service.py',
        'platform_style_service.py',
        'prompt_combination_service.py',
        'prompt_template_service.py',
    ]

    print("=" * 80)
    print("Fixing decorator order issues")
    print("=" * 80)

    fixed_count = 0
    for filename in files_to_check:
        filepath = os.path.join(services_dir, filename)
        if os.path.exists(filepath):
            if fix_decorator_order(filepath):
                fixed_count += 1
        else:
            print(f"\nFile not found: {filepath}")

    print("\n" + "=" * 80)
    print(f"Done! Fixed {fixed_count} files")
    print("=" * 80)

if __name__ == '__main__':
    main()
