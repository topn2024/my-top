#!/usr/bin/env python3
"""检查服务文件中错误放置的装饰器"""
import os
import glob

services_dir = 'services'
files_with_issues = []

for filepath in glob.glob(f'{services_dir}/*.py'):
    if '__pycache__' in filepath:
        continue

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 查找错误模式：代码)@log_service_call或代码@log_service_call
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        if '@log_service_call' in line and not line.strip().startswith('@log_service_call'):
            issues.append((i, line.strip()))

    if issues:
        files_with_issues.append((filepath, issues))

if files_with_issues:
    print("Files with misplaced @log_service_call decorators:")
    print("=" * 80)
    for filepath, issues in files_with_issues:
        print(f"\n{filepath}:")
        for line_num, line in issues:
            print(f"  Line {line_num}: {line[:100]}")
    print(f"\nTotal: {len(files_with_issues)} files with issues")
else:
    print("No issues found! All decorators are properly placed.")
