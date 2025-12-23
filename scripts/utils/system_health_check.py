#!/usr/bin/env python3
"""系统健康检查 - 综合报告"""
import ast
import glob
import re
import os

print("=" * 80)
print("TOP_N 系统健康检查报告")
print("=" * 80)

# 1. 语法检查
print("\n[1/5] Python语法检查...")
python_files = glob.glob('*.py') + glob.glob('services/*.py') + glob.glob('blueprints/*.py')
syntax_errors = []

for filepath in python_files:
    if '__pycache__' in filepath:
        continue
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            ast.parse(f.read())
    except SyntaxError as e:
        syntax_errors.append((filepath, e.lineno, str(e)))

if syntax_errors:
    print(f"  ✗ 发现 {len(syntax_errors)} 个语法错误")
    for f, line, err in syntax_errors:
        print(f"    {f}:{line} - {err}")
else:
    print(f"  ✓ 所有 {len(python_files)} 个Python文件语法正确")

# 2. 日志装饰器覆盖检查
print("\n[2/5] API日志装饰器覆盖检查...")
api_routes = []

for filepath in ['app_with_upload.py'] + glob.glob('blueprints/*.py'):
    if not os.path.exists(filepath):
        continue

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i]
        if '@app.route(' in line or '@bp.route(' in line:
            # 找函数名
            func_name = None
            for j in range(i+1, min(i+15, len(lines))):
                if 'def ' in lines[j]:
                    match = re.search(r'def\s+(\w+)', lines[j])
                    if match:
                        func_name = match.group(1)
                        break

            # 检查从route到def之间是否有@log_api_request
            has_log = False
            for j in range(i, min(i+15, len(lines))):
                if '@log_api_request' in lines[j]:
                    has_log = True
                    break
                if 'def ' in lines[j]:
                    break

            if '/api/' in line:  # 只检查API路由
                api_routes.append({
                    'file': filepath,
                    'function': func_name,
                    'has_log': has_log
                })
        i += 1

with_log = sum(1 for r in api_routes if r['has_log'])
total_api = len(api_routes)

if total_api > 0:
    coverage = (with_log / total_api) * 100
    print(f"  API路由总数: {total_api}")
    print(f"  有日志装饰器: {with_log} ({coverage:.1f}%)")
    if coverage < 100:
        print(f"  ⚠ 缺少日志装饰器: {total_api - with_log} 个")
    else:
        print(f"  ✓ 所有API路由都有日志装饰器")

# 3. 服务层日志装饰器检查
print("\n[3/5] 服务层日志装饰器检查...")
service_methods = []

for filepath in glob.glob('services/*.py'):
    if '__pycache__' in filepath:
        continue

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        # 查找公共方法（不以_开头）
        if re.match(r'\s+def\s+[a-z]\w+\s*\(', line):
            # 检查前一行是否有装饰器
            has_log = i > 0 and '@log_service_call' in lines[i-1]

            # 跳过__init__和property
            if '__init__' in line or '@property' in lines[i-1] if i > 0 else False:
                continue

            func_match = re.search(r'def\s+(\w+)', line)
            if func_match:
                service_methods.append({
                    'file': filepath,
                    'method': func_match.group(1),
                    'has_log': has_log
                })

with_log_service = sum(1 for m in service_methods if m['has_log'])
total_service = len(service_methods)

if total_service > 0:
    coverage_service = (with_log_service / total_service) * 100
    print(f"  服务方法总数: {total_service}")
    print(f"  有日志装饰器: {with_log_service} ({coverage_service:.1f}%)")

# 4. 异常处理检查
print("\n[4/5] 异常处理检查...")
error_returns = []

for filepath in ['app_with_upload.py'] + glob.glob('blueprints/*.py'):
    if not os.path.exists(filepath):
        continue

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for i, line in enumerate(lines, 1):
        if "return jsonify({'error':" in line or 'return jsonify({"error":' in line:
            # 检查是否包含success字段
            if "'success'" not in line and '"success"' not in line:
                error_returns.append((filepath, i))

if error_returns:
    print(f"  ⚠ 发现 {len(error_returns)} 处错误响应缺少success字段")
else:
    print(f"  ✓ 所有错误响应都包含success字段")

# 5. 导入检查
print("\n[5/5] 导入检查...")
import_issues = []

# 检查关键导入
key_imports = [
    ('app_with_upload.py', 'from services.ai_service import remove_markdown_and_ai_traces'),
    ('app_with_upload.py', 'from logger_config import setup_logger, log_api_request'),
]

for filepath, expected_import in key_imports:
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        if expected_import not in content:
            import_issues.append((filepath, expected_import))

if import_issues:
    print(f"  ⚠ 发现 {len(import_issues)} 个导入问题")
    for f, imp in import_issues:
        print(f"    {f}: 缺少 {imp}")
else:
    print(f"  ✓ 关键导入都存在")

# 总结
print("\n" + "=" * 80)
print("健康检查总结")
print("=" * 80)

issues_count = len(syntax_errors) + len(error_returns) + len(import_issues)
if total_api > 0:
    issues_count += (total_api - with_log)

if issues_count == 0:
    print("✅ 系统健康状态良好，未发现严重问题！")
else:
    print(f"⚠️  发现 {issues_count} 个问题需要注意")
    print("\n建议:")
    if syntax_errors:
        print("  - 修复语法错误")
    if total_api > with_log:
        print(f"  - 为剩余 {total_api - with_log} 个API添加日志装饰器")
    if error_returns:
        print(f"  - 为 {len(error_returns)} 处错误响应添加success字段")
    if import_issues:
        print("  - 添加缺失的导入语句")

print("=" * 80)
