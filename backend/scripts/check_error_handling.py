#!/usr/bin/env python3
"""检查所有API路由的异常处理是否返回success: false"""
import re

def check_file(filepath):
    """检查单个文件的异常处理"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')

    issues = []
    in_api_function = False
    api_function_name = ''
    api_line = 0

    for i, line in enumerate(lines, 1):
        # 检测API路由定义
        if '@app.route(' in line or '@bp.route(' in line:
            in_api_function = True
            api_line = i
            # 查找函数名
            for j in range(i, min(i+10, len(lines))):
                if lines[j].strip().startswith('def '):
                    match = re.search(r'def\s+(\w+)\s*\(', lines[j])
                    if match:
                        api_function_name = match.group(1)
                        break

        # 在API函数中检测异常处理
        if in_api_function and 'except' in line:
            # 查找这个except块中的return语句
            indent = len(line) - len(line.lstrip())
            found_return = False
            has_success_false = False

            for j in range(i, min(i+20, len(lines))):
                ret_line = lines[j]
                ret_indent = len(ret_line) - len(ret_line.lstrip())

                # 如果缩进减少，说明离开了except块
                if ret_line.strip() and ret_indent <= indent:
                    break

                # 查找return语句
                if 'return' in ret_line and 'jsonify' in ret_line:
                    found_return = True
                    # 检查是否包含success: false或success=False
                    if "'success': False" in ret_line or '"success": false' in ret_line or "'success':False" in ret_line:
                        has_success_false = True
                        break

            # 如果找到return但没有success: false，记录问题
            if found_return and not has_success_false:
                issues.append({
                    'line': i,
                    'function': api_function_name,
                    'api_line': api_line
                })

            # 重置标记（一个函数可能有多个except）
            in_api_function = False

    return issues

# 检查主应用文件
print("检查 app_with_upload.py...")
issues = check_file('app_with_upload.py')

if issues:
    print(f"\n发现 {len(issues)} 个API路由的异常处理缺少 'success': False")
    print("=" * 80)
    for issue in issues:
        print(f"\n函数: {issue['function']} (API定义在第 {issue['api_line']} 行)")
        print(f"异常处理在第 {issue['line']} 行")
else:
    print("\n✓ 所有API路由的异常处理都正确返回了 success: False")

# 检查蓝图文件
import glob
blueprint_files = glob.glob('blueprints/*.py')

for bp_file in blueprint_files:
    print(f"\n检查 {bp_file}...")
    try:
        issues = check_file(bp_file)
        if issues:
            print(f"  发现 {len(issues)} 个问题:")
            for issue in issues:
                print(f"    - {issue['function']} (第 {issue['line']} 行)")
        else:
            print("  ✓ 无问题")
    except Exception as e:
        print(f"  跳过: {e}")
