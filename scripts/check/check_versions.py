#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查已安装的开发和 AI 库版本
"""

import subprocess
import sys

# 重要的库列表
IMPORTANT_PACKAGES = [
    # 核心工具
    ("pip", "包管理器"),
    ("setuptools", "安装工具"),
    ("wheel", "打包工具"),

    # Web 框架
    ("flask", "Web框架"),
    ("requests", "HTTP客户端"),
    ("fastapi", "异步Web框架"),

    # AI/ML 核心
    ("numpy", "数值计算"),
    ("pandas", "数据分析"),
    ("scikit-learn", "机器学习"),
    ("matplotlib", "数据可视化"),

    # 深度学习
    ("torch", "PyTorch"),
    ("tensorflow", "TensorFlow"),

    # NLP/LLM
    ("transformers", "Hugging Face Transformers"),
    ("openai", "OpenAI SDK"),
    ("langchain", "LangChain"),
    ("tiktoken", "Token计数"),

    # 开发工具
    ("jupyter", "Jupyter Notebook"),
    ("black", "代码格式化"),
    ("pytest", "测试框架"),
    ("pydantic", "数据验证"),

    # 实用工具
    ("tqdm", "进度条"),
    ("rich", "终端美化"),
    ("paramiko", "SSH客户端"),
]

def get_package_version(package_name):
    """获取包版本"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", package_name],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.startswith('Version:'):
                    return line.split(':', 1)[1].strip()
        return "未安装"
    except:
        return "检查失败"

def main():
    print("="*80)
    print("  Python 开发和 AI 库版本检查")
    print("="*80)
    print(f"\nPython 版本: {sys.version}")
    print()

    print(f"{'包名':<25} {'说明':<20} {'版本':<15}")
    print("-"*80)

    for package_name, description in IMPORTANT_PACKAGES:
        version = get_package_version(package_name)
        status = "✓" if version != "未安装" else "✗"
        print(f"{status} {package_name:<24} {description:<20} {version:<15}")

    print()
    print("="*80)
    print("提示: 使用 'pip list --outdated' 查看可更新的包")
    print("="*80)

if __name__ == "__main__":
    main()
