#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地测试登录功能
模拟Flask应用调用login_tester
"""
import sys
import os

# 添加backend路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_login_module_import():
    """测试1: 测试login_tester模块导入"""
    print("="*80)
    print("测试1: 导入login_tester模块")
    print("="*80)
    try:
        from login_tester import LoginTester, test_account_login
        print("✓ 成功导入 LoginTester 和 test_account_login")
        return True
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False

def test_login_tester_initialization():
    """测试2: 测试LoginTester初始化"""
    print("\n" + "="*80)
    print("测试2: LoginTester初始化")
    print("="*80)
    try:
        from login_tester import LoginTester

        # 测试headless模式
        tester = LoginTester(headless=True)
        print("✓ LoginTester实例创建成功 (headless=True)")

        # 测试非headless模式
        tester2 = LoginTester(headless=False)
        print("✓ LoginTester实例创建成功 (headless=False)")

        return True
    except Exception as e:
        print(f"✗ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_webdriver_initialization():
    """测试3: 测试WebDriver初始化（需要Chrome和ChromeDriver）"""
    print("\n" + "="*80)
    print("测试3: WebDriver初始化")
    print("="*80)
    print("注意: 此测试需要本地安装Chrome和ChromeDriver")
    print("如果没有安装，此测试会失败，但不影响其他测试")
    print("-"*80)

    try:
        from login_tester import LoginTester

        tester = LoginTester(headless=True)
        print("尝试初始化WebDriver...")

        result = tester.init_driver()

        if result:
            print("✓ WebDriver初始化成功!")
            print("正在关闭WebDriver...")
            tester.close_driver()
            print("✓ WebDriver关闭成功")
            return True
        else:
            print("✗ WebDriver初始化失败")
            print("  可能原因:")
            print("  - Chrome浏览器未安装")
            print("  - ChromeDriver未安装或版本不匹配")
            print("  - Windows环境可能需要额外配置")
            return False

    except Exception as e:
        print(f"✗ 测试过程出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_login_function_signature():
    """测试4: 测试登录函数接口"""
    print("\n" + "="*80)
    print("测试4: 登录函数接口测试")
    print("="*80)

    try:
        from login_tester import LoginTester
        import inspect

        # 检查test_zhihu_login方法
        tester = LoginTester(headless=True)

        # 获取方法签名
        zhihu_sig = inspect.signature(tester.test_zhihu_login)
        print(f"✓ test_zhihu_login 方法签名: {zhihu_sig}")

        csdn_sig = inspect.signature(tester.test_csdn_login)
        print(f"✓ test_csdn_login 方法签名: {csdn_sig}")

        test_login_sig = inspect.signature(tester.test_login)
        print(f"✓ test_login 方法签名: {test_login_sig}")

        # 检查便捷函数
        from login_tester import test_account_login
        func_sig = inspect.signature(test_account_login)
        print(f"✓ test_account_login 函数签名: {func_sig}")

        return True

    except Exception as e:
        print(f"✗ 接口检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mock_login_call():
    """测试5: 模拟登录调用（不实际连接网站）"""
    print("\n" + "="*80)
    print("测试5: 模拟登录调用流程")
    print("="*80)
    print("注意: 此测试模拟调用流程，不会实际初始化WebDriver")
    print("-"*80)

    try:
        from login_tester import LoginTester

        # 创建测试数据
        test_accounts = [
            {'platform': '知乎', 'username': 'test_user_1', 'password': 'test_pass_1'},
            {'platform': 'CSDN', 'username': 'test_user_2', 'password': 'test_pass_2'},
            {'platform': '微博', 'username': 'test_user_3', 'password': 'test_pass_3'},
        ]

        for account in test_accounts:
            platform = account['platform']
            username = account['username']
            password = account['password']

            print(f"\n测试账号: {platform} - {username}")

            # 检查LoginTester能否创建实例
            tester = LoginTester(headless=True)

            # 检查是否有对应的测试方法
            if platform == '知乎':
                method_name = 'test_zhihu_login'
            elif platform == 'CSDN':
                method_name = 'test_csdn_login'
            else:
                method_name = None

            if method_name and hasattr(tester, method_name):
                print(f"  ✓ 找到测试方法: {method_name}")
            else:
                print(f"  ℹ 暂不支持平台: {platform}")

        print("\n✓ 模拟调用流程测试完成")
        return True

    except Exception as e:
        print(f"✗ 模拟调用失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_handling():
    """测试6: 错误处理测试"""
    print("\n" + "="*80)
    print("测试6: 错误处理")
    print("="*80)

    try:
        from login_tester import LoginTester

        tester = LoginTester(headless=True)

        # 测试WebDriver未初始化时的close_driver
        print("测试: 在未初始化WebDriver时调用close_driver")
        tester.close_driver()  # 不应该抛出异常
        print("✓ 正常处理未初始化的driver")

        # 测试多次close
        print("测试: 多次调用close_driver")
        tester.close_driver()
        tester.close_driver()
        print("✓ 多次调用close_driver不会出错")

        return True

    except Exception as e:
        print(f"✗ 错误处理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_platform_support():
    """测试7: 平台支持检查"""
    print("\n" + "="*80)
    print("测试7: 支持的平台列表")
    print("="*80)

    try:
        from login_tester import LoginTester

        tester = LoginTester(headless=True)

        # 检查支持的平台
        supported_platforms = []
        if hasattr(tester, 'test_zhihu_login'):
            supported_platforms.append('知乎')
        if hasattr(tester, 'test_csdn_login'):
            supported_platforms.append('CSDN')

        print(f"当前支持的平台: {', '.join(supported_platforms)}")
        print(f"支持平台数量: {len(supported_platforms)}")

        if len(supported_platforms) >= 2:
            print("✓ 至少支持2个平台")
            return True
        else:
            print("✗ 支持的平台数量不足")
            return False

    except Exception as e:
        print(f"✗ 平台检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*80)
    print("开始运行本地登录功能测试")
    print("="*80)
    print()

    tests = [
        ("模块导入", test_login_module_import),
        ("LoginTester初始化", test_login_tester_initialization),
        ("WebDriver初始化", test_webdriver_initialization),
        ("登录函数接口", test_login_function_signature),
        ("模拟登录调用", test_mock_login_call),
        ("错误处理", test_error_handling),
        ("平台支持", test_platform_support),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n测试 '{test_name}' 发生未捕获的异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # 打印测试摘要
    print("\n" + "="*80)
    print("测试摘要")
    print("="*80)

    passed = 0
    failed = 0

    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name:20s} : {status}")
        if result:
            passed += 1
        else:
            failed += 1

    print("-"*80)
    print(f"总计: {len(results)} 个测试")
    print(f"通过: {passed} 个")
    print(f"失败: {failed} 个")

    if failed == 0:
        print("\n🎉 所有测试通过！")
    elif failed == 1 and not results[2][1]:  # 只有WebDriver初始化失败
        print("\n⚠️  除了WebDriver初始化测试外，其他测试都通过了")
        print("   WebDriver测试失败是正常的，因为本地可能没有安装Chrome/ChromeDriver")
        print("   在服务器环境中，WebDriver应该能正常工作")
    else:
        print(f"\n⚠️  有 {failed} 个测试失败")

    print("="*80)

if __name__ == "__main__":
    # 设置输出编码
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # 检查依赖
    print("检查Python依赖包...")
    try:
        import selenium
        print(f"[OK] selenium {selenium.__version__}")
    except ImportError:
        print("[X] selenium 未安装")
        print("  请运行: pip install selenium")
        sys.exit(1)

    print()

    # 运行测试
    run_all_tests()
