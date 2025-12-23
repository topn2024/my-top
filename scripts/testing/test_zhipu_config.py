#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试智谱 AI 配置
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from config import Config, get_config

def test_config():
    """测试配置"""
    print("=" * 60)
    print("AI Configuration Test")
    print("=" * 60)

    config = Config()

    print("\n[1] Default AI Provider:")
    print(f"    Provider: {config.DEFAULT_AI_PROVIDER}")

    print("\n[2] Zhipu AI Configuration:")
    print(f"    API Base: {config.ZHIPU_API_BASE}")
    print(f"    Chat URL: {config.ZHIPU_CHAT_URL}")
    print(f"    Model: {config.ZHIPU_MODEL}")
    print(f"    API Key: {'SET' if config.ZHIPU_API_KEY else 'NOT SET (empty)'}")

    print("\n[3] Qianwen AI Configuration (Backup):")
    print(f"    API Base: {config.QIANWEN_API_BASE}")
    print(f"    Chat URL: {config.QIANWEN_CHAT_URL}")
    print(f"    Model: {config.QIANWEN_MODEL}")
    print(f"    API Key: {'SET' if config.QIANWEN_API_KEY else 'NOT SET'}")

    print("\n[4] AIService Provider Selection:")
    from services.ai_service import AIService

    try:
        ai_service = AIService(config)
        print(f"    Active Provider: {ai_service.provider.upper()}")
        print(f"    Active Model: {ai_service.model}")
        print(f"    API Endpoint: {ai_service.chat_url}")
        print(f"    API Key Status: {'SET' if ai_service.api_key else 'NOT SET'}")
    except Exception as e:
        print(f"    [ERROR] Failed to initialize AIService: {e}")

    print("\n" + "=" * 60)
    print("Configuration Check Summary:")
    print("=" * 60)

    issues = []

    if config.DEFAULT_AI_PROVIDER == 'zhipu':
        if not config.ZHIPU_API_KEY:
            issues.append("Zhipu API key is not set (empty string)")
        else:
            print("[OK] Zhipu AI is configured as default provider")
    elif config.DEFAULT_AI_PROVIDER == 'qianwen':
        if not config.QIANWEN_API_KEY:
            issues.append("Qianwen API key is not set")
        else:
            print("[OK] Qianwen AI is configured as default provider")
    else:
        issues.append(f"Unknown AI provider: {config.DEFAULT_AI_PROVIDER}")

    if issues:
        print("\n[WARNING] Issues found:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        print("\nTo set Zhipu API key:")
        print("  export ZHIPU_API_KEY='your-api-key-here'")
        print("\nOr add to your environment variables")
    else:
        print("\n[OK] All configurations are valid!")

    print("=" * 60)


if __name__ == '__main__':
    test_config()
