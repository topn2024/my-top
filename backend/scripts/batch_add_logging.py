#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量为API文件添加专业化日志
"""
import os
import re

# 需要处理的文件及其路由装饰器描述
API_FILES = {
    'analysis_prompt_api.py': {
        "list_prompts": "查询分析提示词列表",
        "get_prompt": "获取分析提示词详情",
        "create_prompt": "创建分析提示词",
        "update_prompt": "更新分析提示词",
        "delete_prompt": "删除分析提示词",
        "activate_prompt": "激活分析提示词",
        "archive_prompt": "归档分析提示词",
    },
    'article_prompt_api.py': {
        "list_prompts": "查询文章提示词列表",
        "get_prompt": "获取文章提示词详情",
        "create_prompt": "创建文章提示词",
        "update_prompt": "更新文章提示词",
        "delete_prompt": "删除文章提示词",
        "activate_prompt": "激活文章提示词",
        "archive_prompt": "归档文章提示词",
    },
    'platform_style_api.py': {
        "list_styles": "查询平台风格列表",
        "get_style": "获取平台风格详情",
        "create_style": "创建平台风格",
        "update_style": "更新平台风格",
        "delete_style": "删除平台风格",
        "activate_style": "激活平台风格",
        "archive_style": "归档平台风格",
    },
    'prompt_combination_api.py': {
        "list_combinations": "查询提示词组合列表",
        "get_combination": "获取提示词组合详情",
        "create_combination": "创建提示词组合",
        "update_combination": "更新提示词组合",
        "delete_combination": "删除提示词组合",
        "test_combination": "测试提示词组合",
    },
    'article_style_api.py': {
        "list_styles": "查询文章风格列表",
        "get_style": "获取文章风格详情",
        "create_style": "创建文章风格",
        "update_style": "更新文章风格",
        "delete_style": "删除文章风格",
    },
}


def update_logger_import(content):
    """更新logger导入语句"""
    # 替换 logging.getLogger 为 setup_logger
    if 'logger = logging.getLogger(__name__)' in content:
        content = content.replace(
            'logger = logging.getLogger(__name__)',
            'logger = setup_logger(__name__)'
        )

    # 添加logger_config导入（如果还没有）
    if 'from logger_config import' not in content:
        # 在第一个import语句后添加
        lines = content.split('\n')
        insert_index = -1

        for i, line in enumerate(lines):
            if line.startswith('import logging'):
                insert_index = i + 1
                break

        if insert_index > 0:
            lines.insert(insert_index, 'from logger_config import setup_logger, log_api_request')
            content = '\n'.join(lines)

    return content


def add_decorator_to_function(content, func_name, description):
    """为函数添加日志装饰器"""
    # 查找函数定义，注意可能有多行装饰器
    pattern = rf'(@[^\n]+\n)*def {func_name}\('

    # 检查是否已经有log_api_request装饰器
    func_match = re.search(pattern, content)
    if not func_match:
        return content

    func_start = func_match.start()
    func_text = func_match.group()

    # 检查前面是否已有log_api_request
    before_func = content[:func_start]
    if '@log_api_request(' in before_func.split('\n')[-10:]:
        return content  # 已经有装饰器了

    # 添加装饰器到def前面
    new_func_text = f'@log_api_request("{description}")\n{func_text}'
    content = content[:func_start] + new_func_text + content[func_match.end():]

    return content


def process_file(filepath, function_descriptions):
    """处理单个文件"""
    print(f"\n处理文件: {filepath}")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # 更新logger导入
        content = update_logger_import(content)

        # 为每个函数添加装饰器
        for func_name, description in function_descriptions.items():
            if f'def {func_name}(' in content:
                print(f"  添加装饰器: {func_name} - {description}")
                content = add_decorator_to_function(content, func_name, description)

        # 只有内容变化时才写回
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  [OK] File updated")
            return True
        else:
            print(f"  [-] No change needed")
            return False

    except Exception as e:
        print(f"  [ERROR] {e}")
        return False


def main():
    """主函数"""
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    blueprints_dir = os.path.join(backend_dir, 'blueprints')

    print("=" * 80)
    print("批量添加专业化日志系统")
    print("=" * 80)

    updated_count = 0

    for filename, func_descriptions in API_FILES.items():
        filepath = os.path.join(blueprints_dir, filename)

        if os.path.exists(filepath):
            if process_file(filepath, func_descriptions):
                updated_count += 1
        else:
            print(f"\n文件不存在: {filepath}")

    print("\n" + "=" * 80)
    print(f"Done! Updated {updated_count} files")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Check modified files")
    print("2. Upload to server")
    print("3. Restart Gunicorn")
    print("4. Verify logging output")


if __name__ == '__main__':
    main()
