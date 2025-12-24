#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TOP_N 完整自动化测试套件运行器
整合所有测试类型：单元测试、API测试、UI测试、端到端测试

使用方法:
    python tests/run_complete_tests.py                    # 运行所有测试
    python tests/run_complete_tests.py --type api        # 只运行API测试
    python tests/run_complete_tests.py --type ui         # 只运行UI测试
    python tests/run_complete_tests.py --type e2e        # 只运行端到端测试
    python tests/run_complete_tests.py --type unit       # 只运行单元测试
    python tests/run_complete_tests.py --quick           # 快速测试(跳过UI)
    python tests/run_complete_tests.py --headless false  # 显示浏览器
"""
import sys
import os
import time
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# 设置UTF-8编码输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_DIR = PROJECT_ROOT / 'backend'
TESTS_DIR = PROJECT_ROOT / 'tests'

# 添加路径
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(BACKEND_DIR))


class TestResult:
    """测试结果类"""
    def __init__(self, name: str):
        self.name = name
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors = []
        self.duration = 0.0
        self.output = ""

    @property
    def total(self):
        return self.passed + self.failed + self.skipped

    @property
    def success_rate(self):
        if self.total == 0:
            return 0.0
        return (self.passed / self.total) * 100

    def to_dict(self):
        return {
            'name': self.name,
            'passed': self.passed,
            'failed': self.failed,
            'skipped': self.skipped,
            'total': self.total,
            'success_rate': self.success_rate,
            'duration': self.duration,
            'errors': self.errors
        }


class TestRunner:
    """测试运行器"""

    def __init__(self, headless: bool = True, verbose: bool = False):
        self.headless = headless
        self.verbose = verbose
        self.results: List[TestResult] = []
        self.start_time = None
        self.end_time = None

        # 设置环境变量
        os.environ['TEST_HEADLESS'] = 'true' if headless else 'false'
        os.environ['TEST_BASE_URL'] = os.environ.get('TEST_BASE_URL', 'http://localhost:3001')

    def run_python_test(self, test_file: Path, test_name: str) -> TestResult:
        """运行Python测试文件"""
        result = TestResult(test_name)
        start = time.time()

        try:
            # 使用subprocess运行测试
            cmd = [sys.executable, str(test_file)]

            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=300,
                cwd=str(PROJECT_ROOT)
            )

            result.output = proc.stdout + proc.stderr
            result.duration = time.time() - start

            # 解析输出统计通过/失败数
            output_lower = result.output.lower()
            pass_count = output_lower.count('[pass]') + output_lower.count('✓') + output_lower.count('passed')
            fail_count = output_lower.count('[fail]') + output_lower.count('✗') + output_lower.count('failed')

            if pass_count > 0:
                result.passed = pass_count
            if fail_count > 0:
                result.failed = fail_count
                # 提取错误信息
                for line in result.output.split('\n'):
                    if 'fail' in line.lower() or 'error' in line.lower():
                        result.errors.append(line.strip())

            # 如果没有明确的通过/失败计数，根据退出码判断
            if result.passed == 0 and result.failed == 0:
                if proc.returncode == 0:
                    result.passed = 1
                else:
                    result.failed = 1

            if self.verbose:
                print(result.output)

        except subprocess.TimeoutExpired:
            result.failed = 1
            result.errors.append(f"测试超时: {test_name}")
            result.duration = 300.0

        except Exception as e:
            result.failed = 1
            result.errors.append(f"测试异常: {str(e)}")
            result.duration = time.time() - start

        return result

    def run_pytest(self, test_path: Path, test_name: str, markers: str = None) -> TestResult:
        """使用pytest运行测试"""
        result = TestResult(test_name)
        start = time.time()

        try:
            cmd = [sys.executable, '-m', 'pytest', str(test_path), '-v', '--tb=short']

            if markers:
                cmd.extend(['-m', markers])

            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=600,
                cwd=str(PROJECT_ROOT)
            )

            result.output = proc.stdout + proc.stderr
            result.duration = time.time() - start

            # 解析pytest输出
            for line in result.output.split('\n'):
                if 'passed' in line and ('failed' in line or 'error' in line or 'warning' in line):
                    # 例如: "5 passed, 2 failed in 10.5s"
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'passed' and i > 0:
                            try:
                                result.passed = int(parts[i-1])
                            except ValueError:
                                pass
                        if part == 'failed' and i > 0:
                            try:
                                result.failed = int(parts[i-1])
                            except ValueError:
                                pass
                elif 'passed' in line and 'failed' not in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'passed' and i > 0:
                            try:
                                result.passed = int(parts[i-1])
                            except ValueError:
                                pass

            if result.passed == 0 and result.failed == 0:
                if proc.returncode == 0:
                    result.passed = 1
                else:
                    result.failed = 1

            if self.verbose:
                print(result.output)

        except subprocess.TimeoutExpired:
            result.failed = 1
            result.errors.append(f"pytest超时: {test_name}")
            result.duration = 600.0

        except Exception as e:
            result.failed = 1
            result.errors.append(f"pytest异常: {str(e)}")
            result.duration = time.time() - start

        return result

    def run_unit_tests(self) -> List[TestResult]:
        """运行单元测试"""
        print("\n" + "=" * 70)
        print("  [1/4] 单元测试 (Unit Tests)")
        print("=" * 70)

        results = []

        # 后端单元测试
        unit_tests = [
            (BACKEND_DIR / 'tests' / 'system_test.py', '系统综合测试'),
            (BACKEND_DIR / 'tests' / 'test_unified_models.py', '模型系统测试'),
            (BACKEND_DIR / 'tests' / 'test_auth_unified.py', '认证系统测试'),
            (BACKEND_DIR / 'tests' / 'final_integration_test.py', '集成测试'),
        ]

        for test_file, test_name in unit_tests:
            if test_file.exists():
                print(f"\n  运行: {test_name}...")
                result = self.run_python_test(test_file, test_name)
                results.append(result)
                self._print_result(result)
            else:
                print(f"  跳过: {test_name} (文件不存在)")

        return results

    def run_api_tests(self) -> List[TestResult]:
        """运行API测试"""
        print("\n" + "=" * 70)
        print("  [2/4] API测试 (API Tests)")
        print("=" * 70)

        results = []

        api_test_dir = TESTS_DIR / 'api'
        if api_test_dir.exists():
            api_tests = list(api_test_dir.glob('test_*.py'))

            for test_file in api_tests:
                test_name = f"API: {test_file.stem}"
                print(f"\n  运行: {test_name}...")
                result = self.run_pytest(test_file, test_name)
                results.append(result)
                self._print_result(result)
        else:
            print("  API测试目录不存在")

        return results

    def run_ui_tests(self) -> List[TestResult]:
        """运行UI测试"""
        print("\n" + "=" * 70)
        print("  [3/4] UI测试 (Browser Automation Tests)")
        print("=" * 70)

        results = []

        ui_test_dir = TESTS_DIR / 'ui'
        if ui_test_dir.exists():
            ui_tests = list(ui_test_dir.glob('test_*.py'))

            for test_file in ui_tests:
                test_name = f"UI: {test_file.stem}"
                print(f"\n  运行: {test_name}...")
                result = self.run_pytest(test_file, test_name)
                results.append(result)
                self._print_result(result)
        else:
            print("  UI测试目录不存在")

        return results

    def run_e2e_tests(self) -> List[TestResult]:
        """运行端到端测试"""
        print("\n" + "=" * 70)
        print("  [4/4] 端到端测试 (End-to-End Tests)")
        print("=" * 70)

        results = []

        e2e_test_dir = TESTS_DIR / 'e2e'
        if e2e_test_dir.exists():
            e2e_tests = list(e2e_test_dir.glob('test_*.py'))

            for test_file in e2e_tests:
                test_name = f"E2E: {test_file.stem}"
                print(f"\n  运行: {test_name}...")
                result = self.run_pytest(test_file, test_name)
                results.append(result)
                self._print_result(result)
        else:
            print("  E2E测试目录不存在")

        return results

    def _print_result(self, result: TestResult):
        """打印单个测试结果"""
        status = "PASS" if result.failed == 0 else "FAIL"
        symbol = "✓" if result.failed == 0 else "✗"

        print(f"    {symbol} {result.name}: {result.passed} 通过, {result.failed} 失败 ({result.duration:.2f}s)")

        if result.errors and self.verbose:
            for error in result.errors[:3]:  # 只显示前3个错误
                print(f"      - {error[:80]}")

    def run_all(self, test_types: List[str] = None) -> Dict[str, Any]:
        """运行所有测试"""
        self.start_time = datetime.now()

        print("\n" + "=" * 70)
        print("  TOP_N 完整自动化测试套件")
        print(f"  执行时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  浏览器模式: {'无头模式' if self.headless else '可视模式'}")
        print("=" * 70)

        all_results = []

        # 确定要运行的测试类型
        if test_types is None:
            test_types = ['unit', 'api', 'ui', 'e2e']

        # 运行测试
        if 'unit' in test_types:
            all_results.extend(self.run_unit_tests())

        if 'api' in test_types:
            all_results.extend(self.run_api_tests())

        if 'ui' in test_types:
            all_results.extend(self.run_ui_tests())

        if 'e2e' in test_types:
            all_results.extend(self.run_e2e_tests())

        self.results = all_results
        self.end_time = datetime.now()

        return self._generate_report()

    def _generate_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        total_passed = sum(r.passed for r in self.results)
        total_failed = sum(r.failed for r in self.results)
        total_skipped = sum(r.skipped for r in self.results)
        total_duration = sum(r.duration for r in self.results)

        report = {
            'summary': {
                'total_suites': len(self.results),
                'total_passed': total_passed,
                'total_failed': total_failed,
                'total_skipped': total_skipped,
                'total_tests': total_passed + total_failed + total_skipped,
                'success_rate': (total_passed / (total_passed + total_failed) * 100) if (total_passed + total_failed) > 0 else 0,
                'duration': total_duration,
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'end_time': self.end_time.isoformat() if self.end_time else None
            },
            'suites': [r.to_dict() for r in self.results]
        }

        # 打印报告
        self._print_report(report)

        return report

    def _print_report(self, report: Dict[str, Any]):
        """打印测试报告"""
        summary = report['summary']

        print("\n" + "=" * 70)
        print("  测试报告总结")
        print("=" * 70)

        print(f"\n  测试套件数: {summary['total_suites']}")
        print(f"  总测试数: {summary['total_tests']}")
        print(f"  通过: {summary['total_passed']}")
        print(f"  失败: {summary['total_failed']}")
        print(f"  跳过: {summary['total_skipped']}")
        print(f"  通过率: {summary['success_rate']:.1f}%")
        print(f"  总耗时: {summary['duration']:.2f}秒")

        print("\n  详细结果:")
        print("  " + "-" * 60)

        for suite in report['suites']:
            status = "✓" if suite['failed'] == 0 else "✗"
            print(f"    {status} {suite['name']}: {suite['passed']}/{suite['total']} 通过 ({suite['duration']:.2f}s)")

        print("\n" + "=" * 70)
        if summary['total_failed'] == 0:
            print("  🎉 所有测试通过！")
        else:
            print(f"  ⚠️  有 {summary['total_failed']} 个测试失败")
        print("=" * 70)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='TOP_N 完整自动化测试套件')

    parser.add_argument('--type', '-t',
                       choices=['unit', 'api', 'ui', 'e2e', 'all'],
                       default='all',
                       help='测试类型 (默认: all)')

    parser.add_argument('--headless',
                       type=str,
                       default='true',
                       help='是否使用无头模式 (true/false, 默认: true)')

    parser.add_argument('--quick', '-q',
                       action='store_true',
                       help='快速模式 (跳过UI和E2E测试)')

    parser.add_argument('--verbose', '-v',
                       action='store_true',
                       help='详细输出')

    args = parser.parse_args()

    # 解析headless参数
    headless = args.headless.lower() == 'true'

    # 创建测试运行器
    runner = TestRunner(headless=headless, verbose=args.verbose)

    # 确定测试类型
    if args.quick:
        test_types = ['unit', 'api']
    elif args.type == 'all':
        test_types = ['unit', 'api', 'ui', 'e2e']
    else:
        test_types = [args.type]

    # 运行测试
    report = runner.run_all(test_types)

    # 返回退出码
    if report['summary']['total_failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
