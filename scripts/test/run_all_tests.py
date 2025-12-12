#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行所有本地测试
"""
import sys
import os
import subprocess

def run_test_script(script_name, description):
    """运行单个测试脚本"""
    print("\n" + "="*100)
    print(f"运行: {description}")
    print("="*100)

    try:
        result = subprocess.run(
            [sys.executable, script_name],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=False,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        print(f"运行测试脚本失败: {e}")
        return False

def main():
    """主函数"""
    print("="*100)
    print(" "*35 + "TOP_N 登录功能测试套件")
    print("="*100)

    tests = [
        ("local_test_login.py", "登录模块功能测试"),
        ("local_test_api.py", "Flask API测试"),
    ]

    print("\n将运行以下测试:")
    for i, (script, desc) in enumerate(tests, 1):
        print(f"  {i}. {desc} ({script})")

    print("\n开始测试...\n")

    results = []
    for script, desc in tests:
        script_path = os.path.join(os.path.dirname(__file__), script)
        if not os.path.exists(script_path):
            print(f"\n⚠️  测试脚本不存在: {script_path}")
            results.append((desc, False))
            continue

        success = run_test_script(script, desc)
        results.append((desc, success))

    # 打印总体摘要
    print("\n" + "="*100)
    print(" "*40 + "总体测试摘要")
    print("="*100)

    passed = sum(1 for _, success in results if success)
    failed = len(results) - passed

    for desc, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{desc:40s} : {status}")

    print("-"*100)
    print(f"总计: {len(results)} 个测试套件")
    print(f"通过: {passed} 个")
    print(f"失败: {failed} 个")

    if failed == 0:
        print("\n🎉 所有测试套件都通过了！")
        print("\n登录功能已在本地验证通过，可以部署到服务器。")
    else:
        print(f"\n⚠️  有 {failed} 个测试套件失败，请检查具体错误信息")

    print("="*100)

    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
