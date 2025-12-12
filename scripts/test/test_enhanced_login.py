#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, '/home/u_topn/TOP_N/backend')
os.environ['DISPLAY'] = ':99'

from login_tester_enhanced import LoginTesterEnhanced
import logging
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

print("="*80)
print("测试增强版登录功能")
print("="*80)

# 创建测试器实例 (使用反检测模式)
tester = LoginTesterEnhanced(headless=True, use_undetected=True)

# 测试登录 (使用测试账号)
result = tester.test_zhihu_login(
    username="13751156900",
    password="test_password",
    use_cookie=True,
    max_retries=1
)

print("\n" + "="*80)
print("测试结果:")
print(json.dumps(result, indent=2, ensure_ascii=False))
print("="*80)

tester.quit_driver()
