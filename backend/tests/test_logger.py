#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志系统测试脚本
测试增强版日志功能
"""
import sys
import os
import time
import io

# 设置UTF-8编码输出
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logger_config import (
    setup_logger,
    log_function_call,
    log_service_call,
    log_database_query,
    set_request_id,
    get_request_id,
    clear_request_id
)


# 测试1: 基本日志记录
def test_basic_logging():
    """测试基本日志记录"""
    print("\n" + "=" * 80)
    print("测试 1: 基本日志记录")
    print("=" * 80)

    logger = setup_logger('test.basic')

    logger.debug("这是一条DEBUG日志")
    logger.info("这是一条INFO日志")
    logger.warning("这是一条WARNING日志")
    logger.error("这是一条ERROR日志")

    print("✓ 基本日志记录测试完成")


# 测试2: 请求ID追踪
def test_request_id():
    """测试请求ID追踪"""
    print("\n" + "=" * 80)
    print("测试 2: 请求ID追踪")
    print("=" * 80)

    logger = setup_logger('test.request_id')

    # 设置请求ID
    req_id = set_request_id('TEST-001')
    logger.info(f"设置请求ID: {req_id}")

    # 获取请求ID
    current_id = get_request_id()
    logger.info(f"当前请求ID: {current_id}")

    # 清除请求ID
    clear_request_id()
    logger.info(f"清除后的请求ID: {get_request_id()}")

    print("✓ 请求ID追踪测试完成")


# 测试3: 函数调用日志
@log_function_call(log_args=True)
def sample_function(a, b, c=10):
    """示例函数"""
    time.sleep(0.5)  # 模拟耗时操作
    return a + b + c


def test_function_call_logging():
    """测试函数调用日志"""
    print("\n" + "=" * 80)
    print("测试 3: 函数调用日志")
    print("=" * 80)

    set_request_id('TEST-002')
    result = sample_function(1, 2, c=3)
    print(f"函数返回值: {result}")
    clear_request_id()

    print("✓ 函数调用日志测试完成")


# 测试4: 服务层调用日志
@log_service_call("计算订单总价", log_args=True)
def calculate_order_total(items, discount=0):
    """计算订单总价"""
    time.sleep(0.3)
    total = sum(item['price'] * item['quantity'] for item in items)
    return total * (1 - discount)


def test_service_call_logging():
    """测试服务层调用日志"""
    print("\n" + "=" * 80)
    print("测试 4: 服务层调用日志")
    print("=" * 80)

    set_request_id('TEST-003')
    items = [
        {'name': '商品A', 'price': 100, 'quantity': 2},
        {'name': '商品B', 'price': 50, 'quantity': 3},
    ]
    total = calculate_order_total(items, discount=0.1)
    print(f"订单总价: {total}")
    clear_request_id()

    print("✓ 服务层调用日志测试完成")


# 测试5: 数据库查询日志
@log_database_query("查询用户列表")
def query_users():
    """查询用户"""
    time.sleep(0.2)
    return [{'id': 1, 'name': 'User1'}, {'id': 2, 'name': 'User2'}]


def test_database_query_logging():
    """测试数据库查询日志"""
    print("\n" + "=" * 80)
    print("测试 5: 数据库查询日志")
    print("=" * 80)

    set_request_id('TEST-004')
    users = query_users()
    print(f"查询到 {len(users)} 个用户")
    clear_request_id()

    print("✓ 数据库查询日志测试完成")


# 测试6: 慢查询检测
@log_service_call("慢速操作", log_args=False)
def slow_operation():
    """慢速操作"""
    time.sleep(4)  # 超过慢查询阈值
    return "完成"


def test_slow_query_detection():
    """测试慢查询检测"""
    print("\n" + "=" * 80)
    print("测试 6: 慢查询检测")
    print("=" * 80)

    set_request_id('TEST-005')
    result = slow_operation()
    print(f"慢速操作结果: {result}")
    clear_request_id()

    print("✓ 慢查询检测测试完成")


# 测试7: 异常日志记录
@log_function_call()
def function_with_error():
    """会抛出异常的函数"""
    time.sleep(0.1)
    raise ValueError("这是一个测试异常")


def test_exception_logging():
    """测试异常日志记录"""
    print("\n" + "=" * 80)
    print("测试 7: 异常日志记录")
    print("=" * 80)

    set_request_id('TEST-006')
    try:
        function_with_error()
    except ValueError as e:
        print(f"捕获到异常: {e}")
    clear_request_id()

    print("✓ 异常日志记录测试完成")


# 测试8: 并发请求模拟
def test_concurrent_requests():
    """测试并发请求（模拟多线程）"""
    print("\n" + "=" * 80)
    print("测试 8: 并发请求模拟")
    print("=" * 80)

    logger = setup_logger('test.concurrent')

    # 模拟3个不同的请求
    for i in range(1, 4):
        req_id = set_request_id(f'REQ-{i:03d}')
        logger.info(f"处理请求 {i}")
        time.sleep(0.1)
        logger.info(f"请求 {i} 完成")
        clear_request_id()

    print("✓ 并发请求模拟测试完成")


def main():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("  TOP_N 日志系统测试套件")
    print("=" * 80)

    tests = [
        test_basic_logging,
        test_request_id,
        test_function_call_logging,
        test_service_call_logging,
        test_database_query_logging,
        test_slow_query_detection,
        test_exception_logging,
        test_concurrent_requests,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ 测试失败: {e}")
            failed += 1

    # 总结
    print("\n" + "=" * 80)
    print("  测试总结")
    print("=" * 80)
    print(f"通过: {passed}/{len(tests)}")
    print(f"失败: {failed}/{len(tests)}")

    if failed == 0:
        print("\n✓ 所有测试通过！")
        print("\n提示: 请查看以下日志文件以验证日志内容:")
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        print(f"  - {os.path.join(log_dir, 'all.log')}")
        print(f"  - {os.path.join(log_dir, 'error.log')}")
        print(f"  - {os.path.join(log_dir, 'slow.log')}")
        print(f"  - {os.path.join(log_dir, 'performance.log')}")
        print("\n使用日志分析工具:")
        print(f"  python backend/scripts/log_analyzer.py --tail --lines 100")
        return 0
    else:
        print("\n✗ 部分测试失败")
        return 1


if __name__ == '__main__':
    exit(main())
