#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
升级本地 Python 开发和 AI 开发常用库到最新版本
"""

import subprocess
import sys

# 定义需要升级的包分类
PACKAGES = {
    "核心开发工具": [
        "pip",
        "setuptools",
        "wheel",
    ],

    "Web 开发框架": [
        "flask",
        "flask-cors",
        "django",
        "fastapi",
        "uvicorn",
        "requests",
        "aiohttp",
    ],

    "AI/ML 核心库": [
        "numpy",
        "pandas",
        "scikit-learn",
        "scipy",
        "matplotlib",
        "seaborn",
        "pillow",
    ],

    "深度学习框架": [
        "torch",
        "torchvision",
        "tensorflow",
        "keras",
    ],

    "NLP 和 LLM": [
        "transformers",
        "openai",
        "langchain",
        "langchain-openai",
        "tiktoken",
        "sentence-transformers",
    ],

    "数据处理": [
        "beautifulsoup4",
        "lxml",
        "openpyxl",
        "xlrd",
        "python-docx",
        "PyPDF2",
        "pypdf",
    ],

    "API 和网络": [
        "httpx",
        "websockets",
        "python-dotenv",
        "pydantic",
    ],

    "开发辅助工具": [
        "jupyter",
        "ipython",
        "notebook",
        "black",
        "pylint",
        "pytest",
        "mypy",
    ],

    "SSH 和远程工具": [
        "paramiko",
        "fabric",
    ],

    "其他常用库": [
        "python-dateutil",
        "pytz",
        "tqdm",
        "click",
        "rich",
    ]
}

def upgrade_package(package_name):
    """升级单个包"""
    print(f"\n{'='*60}")
    print(f"正在升级: {package_name}")
    print('='*60)

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", package_name],
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode == 0:
            print(f"✓ {package_name} 升级成功")
            return True, None
        else:
            error = result.stderr or result.stdout
            print(f"✗ {package_name} 升级失败")
            print(f"错误: {error[:200]}")
            return False, error
    except subprocess.TimeoutExpired:
        print(f"✗ {package_name} 升级超时")
        return False, "Timeout"
    except Exception as e:
        print(f"✗ {package_name} 升级异常: {e}")
        return False, str(e)

def main():
    print("="*60)
    print("  升级 Python 开发和 AI 开发常用库")
    print("="*60)
    print(f"\nPython 版本: {sys.version}")
    print(f"pip 版本: {subprocess.check_output([sys.executable, '-m', 'pip', '--version']).decode().strip()}")
    print()

    # 询问用户要升级哪些类别
    print("可用的包类别:")
    categories = list(PACKAGES.keys())
    for i, category in enumerate(categories, 1):
        count = len(PACKAGES[category])
        print(f"  {i}. {category} ({count} 个包)")

    print(f"  {len(categories) + 1}. 全部升级")
    print(f"  0. 退出")

    choice = input(f"\n请选择要升级的类别 (1-{len(categories) + 1}, 多个用逗号分隔, 或输入 0 退出): ").strip()

    if choice == '0':
        print("已取消升级")
        return

    # 确定要升级的包
    packages_to_upgrade = []

    if choice == str(len(categories) + 1):
        # 全部升级
        for category_packages in PACKAGES.values():
            packages_to_upgrade.extend(category_packages)
    else:
        # 选择性升级
        try:
            choices = [int(c.strip()) for c in choice.split(',')]
            for c in choices:
                if 1 <= c <= len(categories):
                    category_name = categories[c - 1]
                    packages_to_upgrade.extend(PACKAGES[category_name])
                    print(f"已选择: {category_name}")
        except ValueError:
            print("输入格式错误，将升级所有包")
            for category_packages in PACKAGES.values():
                packages_to_upgrade.extend(category_packages)

    # 去重
    packages_to_upgrade = list(dict.fromkeys(packages_to_upgrade))

    print(f"\n总共将升级 {len(packages_to_upgrade)} 个包")
    confirm = input("确认开始升级? (y/n): ").strip().lower()

    if confirm != 'y':
        print("已取消升级")
        return

    # 开始升级
    success_count = 0
    failed_count = 0
    failed_packages = []

    for package in packages_to_upgrade:
        success, error = upgrade_package(package)
        if success:
            success_count += 1
        else:
            failed_count += 1
            failed_packages.append((package, error))

    # 总结
    print("\n" + "="*60)
    print("  升级完成!")
    print("="*60)
    print(f"\n总计: {len(packages_to_upgrade)} 个包")
    print(f"成功: {success_count} 个")
    print(f"失败: {failed_count} 个")

    if failed_packages:
        print("\n失败的包:")
        for pkg, error in failed_packages:
            print(f"  - {pkg}")
            if error and error != "Timeout":
                print(f"    原因: {error[:100]}")

    print("\n建议:")
    print("  - 如果有包升级失败，可以单独尝试: pip install --upgrade <package>")
    print("  - 某些包可能需要特定版本，请根据项目需求调整")
    print("  - PyTorch 和 TensorFlow 可能需要根据 CUDA 版本选择对应版本")

if __name__ == "__main__":
    main()
