#!/usr/bin/env python3
"""批量修复所有错误响应，确保包含success: False字段"""
import re

def fix_file(filepath):
    """修复文件中的错误响应"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    fixed_count = 0

    # 模式1: return jsonify({'error': ...})
    # 替换为: return jsonify({'success': False, 'error': ...})
    pattern1 = r"return jsonify\(\{'error':"
    replacement1 = r"return jsonify({'success': False, 'error':"

    # 先检查哪些需要替换（不包含success的）
    lines = content.split('\n')
    new_lines = []

    for line in lines:
        if "return jsonify({'error':" in line and "'success'" not in line and '"success"' not in line:
            # 替换这一行
            new_line = line.replace("return jsonify({'error':", "return jsonify({'success': False, 'error':")
            new_lines.append(new_line)
            fixed_count += 1
            print(f"  修复: {line.strip()[:80]}")
        elif 'return jsonify({"error":' in line and "'success'" not in line and '"success"' not in line:
            # 双引号版本
            new_line = line.replace('return jsonify({"error":', 'return jsonify({"success": false, "error":')
            new_lines.append(new_line)
            fixed_count += 1
            print(f"  修复: {line.strip()[:80]}")
        else:
            new_lines.append(line)

    content = '\n'.join(new_lines)

    if fixed_count > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"\n✓ {filepath}: 修复了 {fixed_count} 处错误响应\n")
        return fixed_count
    else:
        print(f"  {filepath}: 无需修复\n")
        return 0

# 修复主文件
print("修复 app_with_upload.py...")
total = fix_file('app_with_upload.py')

# 修复蓝图文件
import glob
blueprint_files = glob.glob('blueprints/*.py')

for bp_file in blueprint_files:
    if '__pycache__' in bp_file:
        continue
    print(f"修复 {bp_file}...")
    try:
        count = fix_file(bp_file)
        total += count
    except Exception as e:
        print(f"  跳过: {e}\n")

print(f"\n总计修复: {total} 处错误响应")
