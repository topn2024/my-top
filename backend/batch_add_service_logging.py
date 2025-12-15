#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量为服务层文件添加专业化日志
"""
import os
import re

# 需要处理的服务文件及其关键方法
SERVICE_FILES = {
    'ai_service.py': {
        '_call_api': 'AI API调用',
        'analyze_company': '分析公司信息',
        'analyze_company_with_template': '使用模板分析公司',
        'generate_articles': '生成推广文章',
        'generate_articles_with_template': '使用模板生成文章',
    },
    'ai_service_v2.py': {
        'analyze_with_prompt': '使用新提示词分析',
        'generate_articles_with_prompts': '使用新提示词生成文章',
        '_call_ai_with_retry': 'AI调用（含重试）',
    },
    'workflow_service.py': {
        'save_workflow': '保存工作流',
        'get_current_workflow': '获取当前工作流',
        'get_workflow_list': '获取工作流列表',
        'save_articles': '保存文章',
    },
    'publish_service.py': {
        'publish_to_platform': '发布到平台',
        'get_publish_history': '获取发布历史',
        'save_publish_record': '保存发布记录',
    },
    'task_queue_manager.py': {
        'create_publish_task': '创建发布任务',
        'create_batch_tasks': '批量创建任务',
        'get_task_status': '查询任务状态',
        'cancel_task': '取消任务',
        'retry_task': '重试任务',
    },
    'account_service.py': {
        'add_account': '添加平台账号',
        'get_user_accounts': '获取用户账号列表',
        'delete_account': '删除账号',
        'test_account': '测试账号连接',
    },
    'file_service.py': {
        'save_file': '保存上传文件',
        'extract_text': '提取文件文本',
    },
    'analysis_prompt_service.py': {
        'create_prompt': '创建分析提示词',
        'update_prompt': '更新分析提示词',
        'get_prompt': '获取分析提示词',
        'list_prompts': '查询分析提示词列表',
    },
    'article_prompt_service.py': {
        'create_prompt': '创建文章提示词',
        'update_prompt': '更新文章提示词',
        'get_prompt': '获取文章提示词',
        'list_prompts': '查询文章提示词列表',
    },
    'platform_style_service.py': {
        'create_style': '创建平台风格',
        'update_style': '更新平台风格',
        'get_style': '获取平台风格',
        'list_styles': '查询平台风格列表',
    },
    'prompt_template_service.py': {
        'create_template': '创建提示词模板',
        'update_template': '更新提示词模板',
        'get_template': '获取提示词模板',
        'list_templates': '查询提示词模板列表',
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
            # 添加sys和os导入（如果没有）
            if 'import sys' not in content:
                lines.insert(insert_index, 'import sys')
                insert_index += 1
            if 'import os' not in content:
                lines.insert(insert_index, 'import os')
                insert_index += 1

            # 添加路径设置
            lines.insert(insert_index, '\nsys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))')
            insert_index += 1

            # 添加logger_config导入
            lines.insert(insert_index, 'from logger_config import setup_logger, log_service_call')
            content = '\n'.join(lines)

    return content


def add_decorator_to_method(content, method_name, description):
    """为方法添加日志装饰器"""
    # 查找方法定义（类方法或函数）
    # 匹配: def method_name( 或者多个装饰器后的 def method_name(
    patterns = [
        rf'(@[^\n]+\n)*\s+def {method_name}\(',  # 类方法（有缩进）
        rf'(@[^\n]+\n)*def {method_name}\(',      # 模块函数（无缩进）
    ]

    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            func_start = match.start()
            func_text = match.group()

            # 检查前面是否已有log_service_call
            before_func = content[:func_start]
            if '@log_service_call(' in before_func[-200:]:
                return content  # 已经有装饰器了

            # 确定缩进
            indent = ''
            if func_text.startswith(' '):
                # 类方法，保持缩进
                indent = '    '

            # 添加装饰器
            new_func_text = f'{indent}@log_service_call("{description}")\n{func_text}'
            content = content[:func_start] + new_func_text + content[match.end():]

            return content

    return content


def process_file(filepath, method_descriptions):
    """处理单个文件"""
    print(f"\nProcessing: {filepath}")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # 更新logger导入
        content = update_logger_import(content)

        # 为每个方法添加装饰器
        added_count = 0
        for method_name, description in method_descriptions.items():
            if f'def {method_name}(' in content:
                print(f"  Adding decorator: {method_name} - {description}")
                new_content = add_decorator_to_method(content, method_name, description)
                if new_content != content:
                    added_count += 1
                    content = new_content

        # 只有内容变化时才写回
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  [OK] File updated - {added_count} decorators added")
            return True
        else:
            print(f"  [-] No change needed")
            return False

    except Exception as e:
        print(f"  [ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    services_dir = os.path.join(backend_dir, 'services')

    print("=" * 80)
    print("Batch adding professional logging to service layer")
    print("=" * 80)

    updated_count = 0

    for filename, method_descriptions in SERVICE_FILES.items():
        filepath = os.path.join(services_dir, filename)

        if os.path.exists(filepath):
            if process_file(filepath, method_descriptions):
                updated_count += 1
        else:
            print(f"\nFile not found: {filepath}")

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
