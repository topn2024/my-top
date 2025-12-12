#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试发布流程 - 完整日志输出
"""
import sys
import os

# 添加 backend 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# 设置日志
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

from zhihu_auto_post_enhanced import post_article_to_zhihu

print("=" * 80)
print("开始测试知乎发布")
print("=" * 80)

# 测试发布
result = post_article_to_zhihu(
    username='admin',
    title='测试文章：AI智能体技术探索',
    content='''这是一篇测试文章的内容。

第一段：介绍AI智能体的基本概念和发展历史。

第二段：讨论当前AI智能体领域的技术挑战。

第三段：展望未来AI智能体的应用前景。''',
    password=None  # 使用 Cookie 登录
)

print("\n" + "=" * 80)
print("发布结果：")
print("=" * 80)
print(f"成功: {result.get('success')}")
print(f"消息: {result.get('message')}")
print(f"URL: {result.get('url')}")
print(f"错误: {result.get('error')}")
