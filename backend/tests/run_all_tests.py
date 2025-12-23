#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行所有测试套件
生成完整的测试报告
"""
import sys
import os
from pathlib import Path
import subprocess
from datetime import datetime

# 设置UTF-8编码输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))


def run_test_suite(test_file, suite_name):
    """运行单个测试套件"""
    print(f"\n{'='*70}")
    print(f"  运行测试套件: {suite_name}")
    print(f"{'='*70}")

    try:
        # 使用完整的Python路径
        python_exe = r"D:\Python3.13.1\python.exe"
        result = subprocess.run(
            [python_exe, test_file],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        # 打印输出
        print(result.stdout)
        if result.stderr:
            print(result.stderr)

        # 检查退出码
        if result.returncode == 0:
            print(f"\n✅ {suite_name} - 全部通过")
            return True, result.stdout
        else:
            print(f"\n❌ {suite_name} - 部分失败")
            return False, result.stdout

    except Exception as e:
        print(f"\n❌ {suite_name} - 运行异常: {e}")
        return False, str(e)


def generate_report(results):
    """生成测试报告"""
    print("\n" + "="*70)
    print("  最终测试报告")
    print("="*70)

    total_suites = len(results)
    passed_suites = sum(1 for success, _ in results.values() if success)

    print(f"\n测试套件总数: {total_suites}")
    print(f"通过套件数: {passed_suites}")
    print(f"失败套件数: {total_suites - passed_suites}")
    print(f"通过率: {passed_suites/total_suites*100:.1f}%")

    print("\n详细结果:")
    for suite_name, (success, output) in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {status} - {suite_name}")

    # 统计总测试数
    total_tests = 0
    for suite_name, (success, output) in results.items():
        if "通过:" in output:
            # 提取通过数（格式：通过: X/Y）
            for line in output.split('\n'):
                if line.startswith('通过:'):
                    parts = line.split(':')[1].strip().split('/')
                    if len(parts) == 2:
                        total_tests += int(parts[1])
                        break

    print(f"\n总测试用例数: {total_tests}")

    if passed_suites == total_suites:
        print("\n" + "="*70)
        print("  🎉 所有测试套件通过！")
        print("  系统完全健康，可以安全投入生产使用。")
        print("="*70)
        return True
    else:
        print("\n" + "="*70)
        print("  ⚠️  部分测试套件失败")
        print("  请检查失败的测试并修复问题。")
        print("="*70)
        return False


def main():
    """主函数"""
    print("="*70)
    print("  TOP_N 完整测试套件")
    print(f"  执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

    # 定义所有测试套件
    test_suites = {
        "系统综合测试": "backend/tests/system_test.py",
        "模型系统测试": "backend/tests/test_unified_models.py",
        "认证系统测试": "backend/tests/test_auth_unified.py",
        "集成测试": "backend/tests/final_integration_test.py"
    }

    # 运行所有测试
    results = {}
    for suite_name, test_file in test_suites.items():
        success, output = run_test_suite(test_file, suite_name)
        results[suite_name] = (success, output)

    # 生成报告
    all_passed = generate_report(results)

    return 0 if all_passed else 1


if __name__ == '__main__':
    exit(main())
