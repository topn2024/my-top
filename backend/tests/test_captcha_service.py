#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云码验证码识别服务测试脚本
测试captcha_service.py模块的各项功能
"""
import sys
import os
import io

# 设置stdout编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.captcha_service import CaptchaService, recognize_captcha


def test_service_init():
    """测试服务初始化"""
    print("=" * 50)
    print("测试1: 服务初始化")
    print("=" * 50)

    # 不带token初始化（从配置文件读取）
    service = CaptchaService()
    if service.token:
        print(f"✓ 从配置文件读取token成功: {service.token[:10]}...")
    else:
        print("⚠ 未配置token，请在 config/captcha_config.json 中配置 jfbym_token")

    # 带token初始化
    service2 = CaptchaService(token="test_token")
    print(f"✓ 直接传入token初始化成功: {service2.token}")

    return service


def test_get_balance(service):
    """测试获取余额"""
    print("\n" + "=" * 50)
    print("测试2: 获取账户余额")
    print("=" * 50)

    if not service.token:
        print("✗ 未配置token，跳过余额查询测试")
        return False

    success, balance, data = service.get_balance()

    if success:
        print(f"✓ 余额查询成功: {balance} 元")
        return True
    else:
        print(f"✗ 余额查询失败: {data}")
        return False


def test_recognize_common(service, image_path=None):
    """测试通用验证码识别"""
    print("\n" + "=" * 50)
    print("测试3: 通用验证码识别")
    print("=" * 50)

    if not service.token:
        print("✗ 未配置token，跳过识别测试")
        return False

    if not image_path:
        print("⚠ 未提供测试图片路径，跳过识别测试")
        print("  用法: python test_captcha_service.py <验证码图片路径>")
        return False

    if not os.path.exists(image_path):
        print(f"✗ 图片文件不存在: {image_path}")
        return False

    print(f"正在识别图片: {image_path}")

    success, result, data = service.recognize_common(image_path=image_path)

    if success:
        print(f"✓ 识别成功: {result}")
        print(f"  完整响应: {data}")
        return True
    else:
        print(f"✗ 识别失败: {result}")
        print(f"  完整响应: {data}")
        return False


def test_quick_recognize(image_path=None):
    """测试快捷识别函数"""
    print("\n" + "=" * 50)
    print("测试4: 快捷识别函数")
    print("=" * 50)

    if not image_path:
        print("⚠ 未提供测试图片路径，跳过快捷识别测试")
        return False

    if not os.path.exists(image_path):
        print(f"✗ 图片文件不存在: {image_path}")
        return False

    print(f"使用快捷函数识别: {image_path}")

    success, result = recognize_captcha(image_path=image_path)

    if success:
        print(f"✓ 快捷识别成功: {result}")
        return True
    else:
        print(f"✗ 快捷识别失败: {result}")
        return False


def test_captcha_types():
    """展示支持的验证码类型"""
    print("\n" + "=" * 50)
    print("支持的验证码类型")
    print("=" * 50)

    types = {
        'TYPE_COMMON_ALPHANUMERIC': ('10110', '通用数英混合'),
        'TYPE_COMMON_CHINESE': ('10111', '通用中文'),
        'TYPE_COMMON_ARITHMETIC': ('10112', '通用算术'),
        'TYPE_SLIDE_PUZZLE': ('20110', '通用滑块拼图'),
        'TYPE_CLICK_CHINESE': ('30100', '通用文字点选'),
        'TYPE_CLICK_ICON': ('30101', '通用图标点选'),
        'TYPE_RECAPTCHA_V2': ('40010', '谷歌reCaptcha v2'),
        'TYPE_RECAPTCHA_V3': ('40011', '谷歌reCaptcha v3'),
    }

    for name, (code, desc) in types.items():
        print(f"  {name}: {code} - {desc}")


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("       云码验证码识别服务测试")
    print("       API文档: https://www.jfbym.com/demo.html")
    print("=" * 60)

    # 获取测试图片路径（可选）
    image_path = sys.argv[1] if len(sys.argv) > 1 else None

    # 运行测试
    service = test_service_init()
    test_captcha_types()

    if service.token:
        test_get_balance(service)
        test_recognize_common(service, image_path)
        test_quick_recognize(image_path)
    else:
        print("\n" + "-" * 50)
        print("提示: 请先配置API密钥")
        print("1. 注册云码账号: https://www.jfbym.com/")
        print("2. 获取API密钥")
        print("3. 编辑 backend/config/captcha_config.json")
        print('   将 "jfbym_token": "" 改为 "jfbym_token": "你的密钥"')
        print("-" * 50)

    print("\n测试完成!")


if __name__ == '__main__':
    main()
