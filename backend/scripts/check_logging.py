#!/usr/bin/env python3
"""检查哪些API路由缺少日志装饰器"""
import re

with open('app_with_upload.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

routes_without_log = []

for i, line in enumerate(lines):
    if '@app.route(' in line and '/api/' in line:
        # 检查前面3行是否有@log_api_request
        has_log = False
        for j in range(max(0, i-3), i):
            if '@log_api_request' in lines[j]:
                has_log = True
                break

        if not has_log:
            route = line.strip()
            # 获取函数名
            func_line = i + 1
            while func_line < len(lines) and not lines[func_line].strip().startswith('def '):
                func_line += 1

            if func_line < len(lines):
                func_name = lines[func_line].strip()
                routes_without_log.append((i+1, route, func_name))

print("API routes without @log_api_request decorator:")
print("=" * 80)
for line_num, route, func_name in routes_without_log:
    print(f"Line {line_num}: {route}")
    print(f"         {func_name}")
    print()

print(f"\nTotal: {len(routes_without_log)} routes without logging")
