#!/usr/bin/env python3
"""检查所有API路由是否有日志装饰器"""
import re
import glob

def check_route_decorators(filepath):
    """检查文件中的路由装饰器"""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    routes = []
    for i, line in enumerate(lines):
        if '@app.route(' in line or '@bp.route(' in line:
            # 查找这个路由的函数名
            func_name = None
            for j in range(i+1, min(i+10, len(lines))):
                if 'def ' in lines[j]:
                    match = re.search(r'def\s+(\w+)\s*\(', lines[j])
                    if match:
                        func_name = match.group(1)
                        break

            # 检查前面几行是否有@log_api_request
            has_log_decorator = False
            for j in range(max(0, i-5), i):
                if '@log_api_request' in lines[j]:
                    has_log_decorator = True
                    break

            routes.append({
                'file': filepath,
                'line': i+1,
                'route': line.strip(),
                'function': func_name,
                'has_logging': has_log_decorator
            })

    return routes

# 检查文件
files = ['app_with_upload.py']
files.extend(glob.glob('blueprints/*.py'))

all_routes = []
for filepath in files:
    try:
        routes = check_route_decorators(filepath)
        all_routes.extend(routes)
    except Exception as e:
        print(f"Error checking {filepath}: {e}")

# 统计
total = len(all_routes)
with_logging = sum(1 for r in all_routes if r['has_logging'])
without_logging = total - with_logging

print(f"\n总共 {total} 个API路由")
print(f"✓ {with_logging} 个有日志装饰器")
print(f"✗ {without_logging} 个缺少日志装饰器")

if without_logging > 0:
    print("\n缺少日志装饰器的路由:")
    print("=" * 80)
    for route in all_routes:
        if not route['has_logging']:
            print(f"\n文件: {route['file']}")
            print(f"行号: {route['line']}")
            print(f"函数: {route['function']}")
            print(f"路由: {route['route']}")
