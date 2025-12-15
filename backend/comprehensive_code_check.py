#!/usr/bin/env python3
"""全面检查代码中的潜在问题"""
import os
import sys
import ast
import glob

def check_python_syntax(filepath):
    """检查Python语法错误"""
    errors = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
        ast.parse(code)
        return None
    except SyntaxError as e:
        return {
            'file': filepath,
            'line': e.lineno,
            'error': str(e),
            'type': 'SyntaxError'
        }
    except Exception as e:
        return {
            'file': filepath,
            'error': str(e),
            'type': type(e).__name__
        }

def check_orphaned_code(filepath):
    """检查孤立的代码块（模块级别的return语句等）"""
    issues = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # 检查模块级别的return语句
            if stripped.startswith('return ') and not line.startswith('    '):
                # 检查前面是否有函数定义
                has_function = False
                for j in range(max(0, i-20), i):
                    if 'def ' in lines[j]:
                        has_function = True
                        break

                if not has_function:
                    issues.append({
                        'file': filepath,
                        'line': i,
                        'issue': 'Orphaned return statement (not in a function)',
                        'code': line.strip()
                    })

        return issues
    except Exception as e:
        return [{'file': filepath, 'error': str(e)}]

def check_docstring_issues(filepath):
    """检查文档字符串问题"""
    issues = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        in_docstring = False
        docstring_start = None

        for i, line in enumerate(lines, 1):
            if '"""' in line or "'''" in line:
                if not in_docstring:
                    in_docstring = True
                    docstring_start = i
                else:
                    in_docstring = False
                    docstring_start = None

        # 如果有未关闭的文档字符串
        if in_docstring:
            issues.append({
                'file': filepath,
                'line': docstring_start,
                'issue': 'Unclosed docstring',
                'code': lines[docstring_start-1].strip()[:60]
            })

        return issues
    except Exception as e:
        return [{'file': filepath, 'error': str(e)}]

def check_import_issues(filepath):
    """检查导入语句问题"""
    issues = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()

        tree = ast.parse(code)

        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append({
                        'line': node.lineno,
                        'module': module,
                        'name': alias.name
                    })

        # 这里可以添加更多检查逻辑
        # 比如检查是否有循环导入等

    except Exception as e:
        pass

    return []

def check_function_completeness(filepath):
    """检查函数定义的完整性"""
    issues = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # 检查def后面是否有完整的函数签名
            if stripped.startswith('def '):
                if ':' not in line:
                    # 函数定义可能跨行
                    found_colon = False
                    for j in range(i, min(i+5, len(lines))):
                        if ':' in lines[j]:
                            found_colon = True
                            break

                    if not found_colon:
                        issues.append({
                            'file': filepath,
                            'line': i,
                            'issue': 'Function definition without colon',
                            'code': line.strip()[:60]
                        })

        return issues
    except Exception as e:
        return [{'file': filepath, 'error': str(e)}]

def main():
    print("=" * 80)
    print("全面代码检查")
    print("=" * 80)

    # 获取所有Python文件
    python_files = []

    # 主目录
    python_files.extend(glob.glob('*.py'))

    # 子目录
    for subdir in ['services', 'blueprints', 'migrations']:
        if os.path.exists(subdir):
            python_files.extend(glob.glob(f'{subdir}/*.py'))

    total_files = len(python_files)
    syntax_errors = []
    orphaned_code = []
    docstring_issues = []
    function_issues = []

    print(f"\n检查 {total_files} 个Python文件...\n")

    for filepath in python_files:
        if '__pycache__' in filepath:
            continue

        # 语法检查
        syntax_err = check_python_syntax(filepath)
        if syntax_err:
            syntax_errors.append(syntax_err)

        # 孤立代码检查
        orphaned = check_orphaned_code(filepath)
        if orphaned:
            orphaned_code.extend(orphaned)

        # 文档字符串检查
        docstring = check_docstring_issues(filepath)
        if docstring:
            docstring_issues.extend(docstring)

        # 函数完整性检查
        func_issues = check_function_completeness(filepath)
        if func_issues:
            function_issues.extend(func_issues)

    # 输出结果
    print("\n" + "=" * 80)
    print("检查结果")
    print("=" * 80)

    if syntax_errors:
        print(f"\n❌ 发现 {len(syntax_errors)} 个语法错误:")
        for err in syntax_errors:
            print(f"\n  文件: {err['file']}")
            if 'line' in err:
                print(f"  行号: {err['line']}")
            print(f"  错误: {err['error']}")
    else:
        print("\n✓ 没有语法错误")

    if orphaned_code:
        print(f"\n⚠ 发现 {len(orphaned_code)} 个孤立代码块:")
        for issue in orphaned_code:
            print(f"\n  文件: {issue['file']}")
            print(f"  行号: {issue['line']}")
            print(f"  问题: {issue['issue']}")
            print(f"  代码: {issue['code']}")
    else:
        print("\n✓ 没有孤立代码块")

    if docstring_issues:
        print(f"\n⚠ 发现 {len(docstring_issues)} 个文档字符串问题:")
        for issue in docstring_issues:
            print(f"\n  文件: {issue['file']}")
            print(f"  行号: {issue['line']}")
            print(f"  问题: {issue['issue']}")
    else:
        print("\n✓ 文档字符串格式正确")

    if function_issues:
        print(f"\n⚠ 发现 {len(function_issues)} 个函数定义问题:")
        for issue in function_issues:
            print(f"\n  文件: {issue['file']}")
            print(f"  行号: {issue['line']}")
            print(f"  问题: {issue['issue']}")
            print(f"  代码: {issue['code']}")
    else:
        print("\n✓ 函数定义完整")

    print("\n" + "=" * 80)
    total_issues = len(syntax_errors) + len(orphaned_code) + len(docstring_issues) + len(function_issues)
    if total_issues == 0:
        print("✅ 所有检查通过！")
    else:
        print(f"⚠️  发现 {total_issues} 个问题需要修复")
    print("=" * 80)

if __name__ == '__main__':
    main()
