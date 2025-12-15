#!/usr/bin/env python3
"""自动修复错误放置的@log_service_call装饰器"""
import os
import glob
import re

services_dir = 'services'
fixed_count = 0

for filepath in glob.glob(f'{services_dir}/*.py'):
    if '__pycache__' in filepath:
        continue

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    original_content = ''.join(lines)
    modified = False

    # 逐行检查并修复
    i = 0
    while i < len(lines):
        line = lines[i]

        # 如果当前行包含错误放置的装饰器
        if '@log_service_call(' in line and not line.strip().startswith('@log_service_call'):
            # 提取装饰器部分
            match = re.search(r'@log_service_call\([^)]+\)', line)
            if match:
                decorator = match.group()
                # 移除这行中的装饰器
                lines[i] = line.replace(decorator, '').rstrip() + '\n'

                # 向前查找方法定义
                # 跳过空行和注释，找到def行
                j = i + 1
                while j < len(lines):
                    next_line = lines[j].strip()
                    if next_line and not next_line.startswith('#') and not next_line.startswith('"""') and not next_line.startswith("'''"):
                        # 找到了下一个非空行
                        if next_line.startswith('def '):
                            # 找到方法定义，在它前面插入装饰器
                            indent = len(lines[j]) - len(lines[j].lstrip())
                            decorator_line = ' ' * indent + decorator + '\n'
                            lines.insert(j, decorator_line)
                            modified = True
                            print(f"Fixed in {filepath} at line {i+1}: moved decorator to line {j+1}")
                            break
                        else:
                            # 这不是方法定义，可能找错了
                            print(f"Warning: {filepath} line {i+1} - next statement is not a function definition")
                            break
                    j += 1

        i += 1

    if modified:
        # 写回文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"  [FIXED] {filepath}")
        fixed_count += 1

print(f"\nTotal: Fixed {fixed_count} files")
