#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试中文编码是否正确
"""
import requests
import json

BASE_URL = "http://39.105.12.124"

# 1. 测试不需要登录的API
print("=" * 60)
print("测试1: AI模型列表API (不需要登录)")
print("=" * 60)
response = requests.get(f"{BASE_URL}/api/models")
print(f"状态码: {response.status_code}")
print(f"响应头Content-Type: {response.headers.get('Content-Type')}")

# 获取原始文本
raw_text = response.text
print(f"\n原始响应文本 (前500字符):")
print(raw_text[:500])

# 检查是否有Unicode转义
if '\\u' in raw_text:
    print("\n❌ 发现Unicode转义序列 - 编码配置未生效!")
else:
    print("\n✅ 没有Unicode转义 - 中文正确显示")

# 解析JSON
try:
    data = response.json()
    if 'models' in data and len(data['models']) > 0:
        first_model = data['models'][0]
        print(f"\n第一个模型:")
        print(f"  name: {first_model.get('name')}")
        print(f"  description: {first_model.get('description')}")
except Exception as e:
    print(f"解析JSON失败: {e}")

print("\n" + "=" * 60)
print("测试2: 登录并获取发布历史")
print("=" * 60)

# 创建session保持cookie
session = requests.Session()

# 登录
login_data = {
    "username": "admin",
    "password": "admin123"
}

login_response = session.post(f"{BASE_URL}/api/auth/login", json=login_data)
print(f"登录状态码: {login_response.status_code}")

if login_response.status_code == 200:
    print("✅ 登录成功")

    # 获取发布历史
    history_response = session.get(f"{BASE_URL}/api/publish_history")
    print(f"\n发布历史API状态码: {history_response.status_code}")

    raw_history = history_response.text
    print(f"\n原始响应 (前800字符):")
    print(raw_history[:800])

    # 检查编码
    if '\\u' in raw_history:
        print("\n❌ 发布历史中发现Unicode转义!")
        # 找出所有转义序列
        import re
        escapes = re.findall(r'\\u[0-9a-fA-F]{4}', raw_history)
        if escapes:
            print(f"发现 {len(set(escapes))} 个不同的Unicode转义序列")
            print(f"示例: {list(set(escapes))[:5]}")
    else:
        print("\n✅ 发布历史中没有Unicode转义")

    # 解析并显示
    try:
        history_data = history_response.json()
        if history_data.get('success') and 'history' in history_data:
            print(f"\n发布历史记录数: {history_data.get('count', 0)}")
            if history_data['history']:
                first_record = history_data['history'][0]
                print(f"\n第一条记录:")
                print(f"  article_title: {first_record.get('article_title')}")
                print(f"  platform: {first_record.get('platform')}")
                print(f"  status: {first_record.get('status')}")
        else:
            print(f"API返回: {history_data}")
    except Exception as e:
        print(f"解析失败: {e}")
else:
    print(f"❌ 登录失败: {login_response.text}")

print("\n" + "=" * 60)
