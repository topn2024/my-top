#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 TOP_N API 功能
"""

import requests
import json

SERVER_URL = "http://39.105.12.124:8080"

def test_health():
    """测试健康检查"""
    print("=" * 60)
    print("测试 1: 健康检查")
    print("=" * 60)

    response = requests.get(f"{SERVER_URL}/api/health")
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()

def test_analyze():
    """测试公司分析功能"""
    print("=" * 60)
    print("测试 2: 公司分析功能")
    print("=" * 60)

    data = {
        "company_name": "测试公司",
        "company_desc": "这是一家专注于人工智能技术的创新型公司，提供智能化解决方案。"
    }

    print(f"请求数据: {json.dumps(data, indent=2, ensure_ascii=False)}")

    try:
        response = requests.post(f"{SERVER_URL}/api/analyze", json=data, timeout=60)
        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"响应成功: {result.get('success')}")
            print(f"分析结果:")
            print(result.get('analysis', ''))[:500] + "..."
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"异常: {e}")
    print()

def test_platforms():
    """测试获取平台列表"""
    print("=" * 60)
    print("测试 3: 获取推荐平台")
    print("=" * 60)

    response = requests.get(f"{SERVER_URL}/api/platforms")
    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        platforms = result.get('platforms', [])
        print(f"平台数量: {len(platforms)}")
        for p in platforms[:3]:
            print(f"  - {p['name']}: {p['description']}")
    print()

def main():
    print("\n" + "=" * 60)
    print("  TOP_N 平台 API 测试")
    print("=" * 60)
    print()

    # 测试 1: 健康检查
    test_health()

    # 测试 2: 获取平台
    test_platforms()

    # 测试 3: 分析功能 (这是之前报错的部分)
    test_analyze()

    print("=" * 60)
    print("  测试完成！")
    print("=" * 60)
    print()

if __name__ == "__main__":
    main()
