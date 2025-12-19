#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码冲突检查脚本
检查路由冲突、重复业务逻辑、Blueprint注册冲突等
"""
import os
import re
from collections import defaultdict
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def print_section(title):
    print('\n' + '=' * 80)
    print(title)
    print('=' * 80)

def check_route_conflicts():
    """检查路由冲突"""
    print_section('路由冲突检查')

    routes = defaultdict(list)

    # Blueprint URL前缀映射
    bp_prefixes = {
        'api_bp': '/api',
        'auth_bp': '/auth',
        'pages_bp': '',
        'task_bp': '/api/tasks',
        'analysis_prompt_bp': '/api/analysis-prompts',
        'article_prompt_bp': '/api/article-prompts',
        'platform_style_bp': '/api/platform-styles',
        'article_style_bp': '/api/article-style',
        'combination_bp': '/api/prompt-combinations',
        'enterprise_bp': '/api/enterprises',
        'csdn_wechat_bp': '',  # 直接在根路径
    }

    # 检查 app_with_upload.py
    try:
        with open('app_with_upload.py', 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i, line in enumerate(lines, 1):
                if '@app.route(' in line:
                    # 提取路由路径
                    path_match = re.search(r"@app\.route\('([^']+)'", line)
                    if path_match:
                        path = path_match.group(1)
                        # 提取方法
                        methods_match = re.search(r"methods=\[([^\]]+)\]", line)
                        if methods_match:
                            methods = methods_match.group(1).replace("'", '').replace('"', '').replace(' ', '')
                        else:
                            methods = 'GET'

                        for method in methods.split(','):
                            key = f'{path}:{method}'
                            routes[key].append(('app_with_upload.py', i, 'app'))
    except FileNotFoundError:
        pass

    # 检查 blueprints 目录
    if os.path.exists('blueprints'):
        for filename in os.listdir('blueprints'):
            if filename.endswith('.py') and not filename.startswith('__'):
                filepath = os.path.join('blueprints', filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        current_bp = None

                        for i, line in enumerate(lines, 1):
                            # 检测Blueprint定义
                            bp_def = re.search(r"(\w+_bp)\s*=\s*Blueprint", line)
                            if bp_def:
                                current_bp = bp_def.group(1)

                            # 检测路由定义
                            if '@' in line and '_bp.route(' in line:
                                bp_match = re.search(r"@(\w+_bp)\.route", line)
                                if bp_match:
                                    bp_name = bp_match.group(1)
                                    current_bp = bp_name

                                    # 提取路由路径
                                    path_match = re.search(r"\.route\('([^']*)'", line)
                                    if path_match:
                                        path = path_match.group(1)

                                        # 获取blueprint前缀
                                        bp_prefix = bp_prefixes.get(bp_name, f'/api/{bp_name.replace("_bp", "")}')

                                        # 组合完整路径
                                        if path:
                                            full_path = bp_prefix + path
                                        else:
                                            full_path = bp_prefix

                                        # 提取HTTP方法
                                        methods_match = re.search(r"methods=\[([^\]]+)\]", line)
                                        if methods_match:
                                            methods = methods_match.group(1).replace("'", '').replace('"', '').replace(' ', '')
                                        else:
                                            methods = 'GET'

                                        for method in methods.split(','):
                                            key = f'{full_path}:{method}'
                                            routes[key].append((filepath, i, bp_name))
                except Exception as e:
                    print(f'读取文件 {filepath} 失败: {e}')

    # 检查冲突
    conflicts = []
    for route, locations in routes.items():
        if len(locations) > 1:
            conflicts.append((route, locations))

    if conflicts:
        print(f'\n⚠️  发现 {len(conflicts)} 个路由冲突:\n')
        for route, locations in sorted(conflicts):
            path, method = route.rsplit(':', 1)
            print(f'🔴 冲突路由: {method} {path}')
            for loc in locations:
                file, line, source = loc
                print(f'   └─ {file}:{line} ({source})')
            print()
    else:
        print('\n✅ 未发现路由冲突')

    return conflicts

def check_blueprint_registration():
    """检查Blueprint注册"""
    print_section('Blueprint 注册检查')

    registrations = defaultdict(list)

    # 检查 app_with_upload.py
    try:
        with open('app_with_upload.py', 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i, line in enumerate(lines, 1):
                if 'register_blueprint' in line:
                    # 提取blueprint名称
                    bp_match = re.search(r"register_blueprint\((\w+)", line)
                    if bp_match:
                        bp_name = bp_match.group(1)
                        registrations[bp_name].append(('app_with_upload.py', i))
    except FileNotFoundError:
        pass

    # 检查重复注册
    duplicates = []
    for bp, locations in registrations.items():
        if len(locations) > 1:
            duplicates.append((bp, locations))

    if duplicates:
        print(f'\n⚠️  发现 {len(duplicates)} 个重复的Blueprint注册:\n')
        for bp, locations in duplicates:
            print(f'🔴 Blueprint: {bp}')
            for loc in locations:
                print(f'   └─ {loc[0]}:{loc[1]}')
            print()
    else:
        print('\n✅ 未发现Blueprint重复注册')

    # 列出所有已注册的Blueprint
    print(f'\n已注册的 Blueprint ({len(registrations)} 个):')
    for bp in sorted(registrations.keys()):
        locations = registrations[bp]
        file, line = locations[0]
        print(f'  ✓ {bp:30} - {file}:{line}')

    return duplicates

def check_duplicate_functions():
    """检查重复的业务逻辑函数"""
    print_section('重复业务逻辑检查')

    functions = defaultdict(list)

    # 要检查的关键函数名模式
    key_patterns = [
        'upload', 'analyze', 'generate_articles', 'publish',
        'login', 'register', 'logout', 'get_user',
        'save_workflow', 'get_workflow', 'create_account'
    ]

    # 检查 app_with_upload.py
    try:
        with open('app_with_upload.py', 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i, line in enumerate(lines, 1):
                if 'def ' in line:
                    func_match = re.search(r"def\s+(\w+)\s*\(", line)
                    if func_match:
                        func_name = func_match.group(1)
                        # 检查是否匹配关键模式
                        for pattern in key_patterns:
                            if pattern in func_name.lower():
                                functions[func_name].append(('app_with_upload.py', i))
                                break
    except FileNotFoundError:
        pass

    # 检查 blueprints
    if os.path.exists('blueprints'):
        for filename in os.listdir('blueprints'):
            if filename.endswith('.py') and not filename.startswith('__'):
                filepath = os.path.join('blueprints', filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        for i, line in enumerate(lines, 1):
                            if 'def ' in line:
                                func_match = re.search(r"def\s+(\w+)\s*\(", line)
                                if func_match:
                                    func_name = func_match.group(1)
                                    for pattern in key_patterns:
                                        if pattern in func_name.lower():
                                            functions[func_name].append((filepath, i))
                                            break
                except Exception:
                    pass

    # 检查重复
    duplicates = []
    for func, locations in functions.items():
        if len(locations) > 1:
            duplicates.append((func, locations))

    if duplicates:
        print(f'\n⚠️  发现 {len(duplicates)} 个可能重复的业务逻辑函数:\n')
        for func, locations in sorted(duplicates):
            print(f'🟡 函数: {func}()')
            for loc in locations:
                print(f'   └─ {loc[0]}:{loc[1]}')
            print()
    else:
        print('\n✅ 未发现明显重复的业务逻辑')

    return duplicates

def check_import_conflicts():
    """检查导入冲突"""
    print_section('导入冲突检查')

    imports = defaultdict(set)

    # 检查 app_with_upload.py
    try:
        with open('app_with_upload.py', 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                if line.strip().startswith('from ') or line.strip().startswith('import '):
                    imports['app_with_upload.py'].add(line.strip())
    except FileNotFoundError:
        pass

    # 统计常见导入
    common_imports = defaultdict(int)
    for file, import_lines in imports.items():
        for imp in import_lines:
            if 'Flask' in imp or 'Blueprint' in imp:
                common_imports[imp] += 1

    print('\n核心导入统计:')
    for imp, count in sorted(common_imports.items()):
        print(f'  {imp}')

def check_config_conflicts():
    """检查配置冲突"""
    print_section('配置冲突检查')

    configs = {}

    # 检查 config.py
    if os.path.exists('config.py'):
        try:
            with open('config.py', 'r', encoding='utf-8') as f:
                content = f.read()
                # 提取配置项
                config_vars = re.findall(r"^([A-Z_]+)\s*=", content, re.MULTILINE)
                configs['config.py'] = set(config_vars)
                print(f'\nconfig.py 中定义了 {len(config_vars)} 个配置项')
        except Exception as e:
            print(f'读取 config.py 失败: {e}')

    # 检查 app_with_upload.py 中的配置覆盖
    try:
        with open('app_with_upload.py', 'r', encoding='utf-8') as f:
            content = f.read()
            # 查找 app.config 设置
            app_configs = re.findall(r"app\.config\['([^']+)'\]", content)
            if app_configs:
                print(f'\napp_with_upload.py 中设置了 {len(set(app_configs))} 个配置项:')
                for cfg in sorted(set(app_configs)):
                    print(f'  - {cfg}')
    except FileNotFoundError:
        pass

def main():
    print('=' * 80)
    print('代码冲突和重复设计检查报告')
    print('=' * 80)
    print(f'检查目录: {os.getcwd()}')

    # 执行各项检查
    route_conflicts = check_route_conflicts()
    bp_duplicates = check_blueprint_registration()
    func_duplicates = check_duplicate_functions()
    check_import_conflicts()
    check_config_conflicts()

    # 总结
    print_section('检查总结')

    total_issues = len(route_conflicts) + len(bp_duplicates) + len(func_duplicates)

    if total_issues > 0:
        print(f'\n🔴 发现 {total_issues} 个潜在问题:')
        print(f'  - 路由冲突: {len(route_conflicts)} 个')
        print(f'  - Blueprint重复注册: {len(bp_duplicates)} 个')
        print(f'  - 重复业务逻辑: {len(func_duplicates)} 个')
        print('\n建议:')
        print('  1. 解决路由冲突，删除重复的路由定义')
        print('  2. 移除 app_with_upload.py 中的重复代码，使用Blueprint版本')
        print('  3. 统一业务逻辑，避免代码重复')
    else:
        print('\n✅ 未发现严重的代码冲突或重复设计问题')

if __name__ == '__main__':
    main()
