#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量升级日志系统脚本
为所有蓝图和服务添加专业化日志
"""
import os
import re

# 需要处理的蓝图文件及其操作描述
BLUEPRINTS = {
    'api.py': {
        '/api/analyze': '分析公司信息',
        '/api/generate_articles': '生成推广文章',
        '/api/publish': '发布文章',
        '/api/workflow': '工作流操作',
    },
    'task_api.py': {
        '/api/tasks': '任务管理',
    },
}

# 日志装饰器配置
LOG_DECORATOR_CONFIGS = {
    # 主要业务API
    'analyze_company': '分析公司信息',
    'generate_articles': '生成推广文章',
    'publish': '发布文章到平台',
    'upload_file': '上传文件',
    'save_workflow': '保存工作流',
    'get_workflow': '获取工作流',

    # 任务API
    'create_task': '创建任务',
    'get_task': '获取任务状态',
    'cancel_task': '取消任务',

    # 账号管理
    'get_accounts': '获取平台账号列表',
    'create_account': '添加平台账号',
    'delete_account': '删除平台账号',
    'test_account': '测试账号连接',
}


def add_logger_import(content):
    """添加日志模块导入"""
    # 检查是否已经导入
    if 'from logger_config import' in content:
        return content

    # 在文件开头的导入部分添加
    import_pattern = r'(from flask import.*?\n)'
    replacement = r'\1from logger_config import setup_logger, log_api_request\n'

    if re.search(import_pattern, content):
        content = re.sub(import_pattern, replacement, content, count=1)
    else:
        # 如果没找到flask导入，在第一个import后添加
        content = re.sub(
            r'(import .*?\n)',
            r'\1from logger_config import setup_logger, log_api_request\n',
            content,
            count=1
        )

    # 替换logger定义
    content = re.sub(
        r'logger = logging\.getLogger\(__name__\)',
        r'logger = setup_logger(__name__)',
        content
    )

    return content


def add_log_decorator(content, function_name, description):
    """为函数添加日志装饰器"""
    # 查找函数定义
    pattern = rf'(@[\w.]+\n)*def {function_name}\('

    # 检查是否已经有log_api_request装饰器
    if f'@log_api_request(' in content:
        return content

    # 添加装饰器
    replacement = f'@log_api_request("{description}")\n' + r'\g<0>'
    content = re.sub(pattern, replacement, content, count=1)

    return content


def process_file(filepath):
    """处理单个文件"""
    print(f"处理文件: {filepath}")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # 添加导入
        content = add_logger_import(content)

        # 根据文件名添加对应的装饰器
        filename = os.path.basename(filepath)

        if filename in BLUEPRINTS:
            for func_name, desc in LOG_DECORATOR_CONFIGS.items():
                if f'def {func_name}(' in content:
                    content = add_log_decorator(content, func_name, desc)

        # 写回文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"  ✓ 完成")
        return True

    except Exception as e:
        print(f"  ✗ 错误: {e}")
        return False


def main():
    """主函数"""
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    blueprints_dir = os.path.join(backend_dir, 'blueprints')

    print("=" * 80)
    print("开始批量升级日志系统")
    print("=" * 80)

    # 处理蓝图文件
    print("\n处理蓝图文件...")
    for filename in BLUEPRINTS.keys():
        filepath = os.path.join(blueprints_dir, filename)
        if os.path.exists(filepath):
            process_file(filepath)

    print("\n" + "=" * 80)
    print("日志系统升级完成")
    print("=" * 80)
    print("\n请手动检查修改的文件，然后:")
    print("1. 上传到服务器")
    print("2. 重启Gunicorn")
    print("3. 查看日志验证效果")


if __name__ == '__main__':
    main()
