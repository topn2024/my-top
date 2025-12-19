#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主测试运行器
提供统一的测试执行入口和报告生成
"""
import sys
import os
import time
import argparse
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.utils.test_helpers import TestTimer, save_test_result
from tests.config.test_config import get_config


class TestRunner:
    """测试运行器类"""

    def __init__(self, config=None):
        """
        初始化测试运行器

        Args:
            config: 测试配置
        """
        self.config = config or get_config()
        self.project_root = project_root
        self.tests_dir = self.project_root / 'tests'
        self.results = []

    def run_all_tests(self, test_type: str = None, coverage: bool = None, parallel: bool = None):
        """
        运行所有测试

        Args:
            test_type: 测试类型 (unit, integration, api, ui, e2e)
            coverage: 是否生成覆盖率报告
            parallel: 是否并行执行
        """
        print("🧪 TOP_N 自动化测试套件")
        print("=" * 70)

        # 使用配置值或参数值
        coverage = coverage if coverage is not None else self.config.get('test.coverage', False)
        parallel = parallel if parallel is not None else self.config.get('test.parallel', False)

        # 确定测试类型
        test_types = self._get_test_types(test_type)

        print(f"📋 测试类型: {', '.join(test_types)}")
        print(f"📊 生成覆盖率: {'是' if coverage else '否'}")
        print(f"⚡ 并行执行: {'是' if parallel else '否'}")
        print()

        # 创建报告目录
        self._setup_report_dirs()

        # 运行测试套件
        total_start_time = time.time()
        overall_success = True

        for test_type_name in test_types:
            print(f"\n🔍 运行 {test_type_name.upper()} 测试套件...")
            print("-" * 50)

            with TestTimer(f"{test_type_name.upper()} 测试"):
                success = self._run_test_suite(test_type_name, coverage, parallel)
                if not success:
                    overall_success = False

        # 生成总报告
        total_duration = time.time() - total_start_time
        self._generate_summary_report(overall_success, total_duration, test_types)

        return overall_success

    def _get_test_types(self, test_type: Optional[str]) -> List[str]:
        """获取测试类型列表"""
        all_types = ['unit', 'integration', 'api', 'ui', 'e2e']

        if test_type is None:
            return all_types
        elif test_type == 'all':
            return all_types
        elif test_type in all_types:
            return [test_type]
        else:
            raise ValueError(f"无效的测试类型: {test_type}. 支持的类型: {all_types}")

    def _setup_report_dirs(self):
        """设置报告目录"""
        reports_dir = self.config.get('paths.reports_dir')
        Path(reports_dir).mkdir(exist_ok=True)

        # 清理旧的HTML报告
        for file in Path(reports_dir).glob("*.html"):
            if not file.name.startswith("report_"):
                file.unlink()

    def _run_test_suite(self, test_type: str, coverage: bool, parallel: bool) -> bool:
        """运行单个测试套件"""
        test_dir = self.tests_dir / test_type

        if not test_dir.exists():
            print(f"⚠️ 测试目录不存在: {test_dir}")
            return True

        # 构建pytest命令
        cmd = self._build_pytest_command(test_type, test_dir, coverage, parallel)

        try:
            # 执行测试
            result = subprocess.run(
                cmd,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=self.config.get('test.timeout', 300)
            )

            # 记录结果
            suite_result = {
                'type': test_type,
                'command': ' '.join(cmd),
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'duration': 0  # 将在TestTimer中设置
            }

            self.results.append(suite_result)

            # 显示结果
            self._display_suite_result(test_type, suite_result)

            return result.returncode == 0

        except subprocess.TimeoutExpired:
            print(f"❌ {test_type.upper()} 测试超时")
            return False
        except Exception as e:
            print(f"❌ {test_type.upper()} 测试执行异常: {e}")
            return False

    def _build_pytest_command(self, test_type: str, test_dir: Path, coverage: bool, parallel: bool) -> List[str]:
        """构建pytest命令"""
        cmd = [sys.executable, "-m", "pytest"]

        # 测试目录
        cmd.append(str(test_dir))

        # 详细输出
        cmd.append("-v")

        # 输出格式
        cmd.extend(["--tb=short", "--strict-markers"])

        # HTML报告
        reports_dir = self.config.get('paths.reports_dir')
        html_report = f"{reports_dir}/report_{test_type}.html"
        cmd.extend(["--html", html_report])

        # JSON报告
        json_report = f"{reports_dir}/report_{test_type}.json"
        cmd.extend(["--json-report", "--json-report-file", json_report])

        # 覆盖率
        if coverage:
            cmd.extend(["--cov=" + self._get_coverage_package(test_type)])
            cmd.extend(["--cov-report", f"html:{reports_dir}/coverage_{test_type}"])
            cmd.extend(["--cov-report", f"xml:{reports_dir}/coverage_{test_type}.xml"])
            cmd.extend(["--cov-report", f"term-missing"])

        # 并行执行
        if parallel:
            import multiprocessing
            workers = min(multiprocessing.cpu_count(), 4)
            cmd.extend(["-n", str(workers)])

        # 标记过滤
        if test_type == 'ui':
            cmd.append("-m ui")
        elif test_type == 'api':
            cmd.append("-m api")
        elif test_type == 'integration':
            cmd.append("-m integration")

        return cmd

    def _get_coverage_package(self, test_type: str) -> str:
        """获取覆盖率包名"""
        coverage_mapping = {
            'unit': 'backend',
            'integration': 'backend',
            'api': 'backend',
            'ui': None,  # UI测试通常不需要覆盖率
            'e2e': None
        }
        return coverage_mapping.get(test_type)

    def _display_suite_result(self, test_type: str, result: Dict[str, Any]):
        """显示测试套件结果"""
        if result['return_code'] == 0:
            print(f"✅ {test_type.upper()} 测试通过")
        else:
            print(f"❌ {test_type.upper()} 测试失败")

        # 显示输出（简化版）
        stdout_lines = result['stdout'].split('\n')
        for line in stdout_lines:
            if 'passed' in line and 'failed' in line:
                print(f"📊 {line.strip()}")
                break

        if result['stderr']:
            error_lines = result['stderr'].split('\n')[:5]  # 只显示前5行错误
            for line in error_lines:
                if line.strip():
                    print(f"⚠️ {line}")

        print()

    def _generate_summary_report(self, overall_success: bool, total_duration: float, test_types: List[str]):
        """生成总结报告"""
        print("=" * 70)
        print("📊 测试总结报告")
        print("=" * 70)

        # 统计信息
        total_suites = len(test_types)
        passed_suites = sum(1 for r in self.results if r['return_code'] == 0)
        failed_suites = total_suites - passed_suites

        print(f"🧪 测试套件总数: {total_suites}")
        print(f"✅ 通过套件: {passed_suites}")
        print(f"❌ 失败套件: {failed_suites}")
        print(f"⏱️ 总执行时间: {total_duration:.2f}秒")

        # 详细结果
        print("\n📋 详细结果:")
        for result in self.results:
            status = "✅ 通过" if result['return_code'] == 0 else "❌ 失败"
            print(f"  {result['type'].upper():10} : {status}")

        # 报告位置
        reports_dir = self.config.get('paths.reports_dir')
        print(f"\n📁 报告位置: {reports_dir}")

        # HTML报告链接
        html_files = list(Path(reports_dir).glob("report_*.html"))
        if html_files:
            print("📄 HTML报告:")
            for html_file in html_files:
                print(f"  - {html_file}")

        # 保存结果
        summary_result = {
            'overall_success': overall_success,
            'total_suites': total_suites,
            'passed_suites': passed_suites,
            'failed_suites': failed_suites,
            'total_duration': total_duration,
            'test_types': test_types,
            'results': self.results,
            'timestamp': time.time()
        }

        save_test_result('test_suite_summary', summary_result)

        # 最终状态
        print("\n" + "=" * 70)
        if overall_success:
            print("🎉 所有测试通过！系统健康状态良好。")
        else:
            print("⚠️ 部分测试失败，请检查详细报告。")
        print("=" * 70)

    def run_quick_tests(self):
        """运行快速测试"""
        print("⚡ 运行快速测试套件...")
        return self.run_all_tests(test_type='unit', coverage=False, parallel=False)

    def run_full_tests(self):
        """运行完整测试"""
        print("🔬 运行完整测试套件...")
        return self.run_all_tests(test_type='all', coverage=True, parallel=True)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='TOP_N 测试运行器')

    parser.add_argument('--type', '-t',
                      choices=['unit', 'integration', 'api', 'ui', 'e2e', 'all'],
                      default='all',
                      help='测试类型')

    parser.add_argument('--coverage', '-c', action='store_true',
                      help='生成覆盖率报告')

    parser.add_argument('--no-coverage', dest='no_coverage', action='store_true',
                      help='不生成覆盖率报告')

    parser.add_argument('--parallel', '-p', action='store_true',
                      help='并行执行测试')

    parser.add_argument('--no-parallel', dest='no_parallel', action='store_true',
                      help='不并行执行测试')

    parser.add_argument('--quick', '-q', action='store_true',
                      help='运行快速测试（仅单元测试）')

    parser.add_argument('--full', '-f', action='store_true',
                      help='运行完整测试套件')

    parser.add_argument('--environment', '-e',
                      choices=['development', 'staging', 'production'],
                      help='测试环境')

    args = parser.parse_args()

    # 加载配置
    config = get_config(args.environment)

    # 确定参数值
    coverage = config.get('test.coverage', False)
    parallel = config.get('test.parallel', False)

    if args.coverage:
        coverage = True
    elif args.no_coverage:
        coverage = False

    if args.parallel:
        parallel = True
    elif args.no_parallel:
        parallel = False

    # 创建测试运行器
    runner = TestRunner(config)

    try:
        # 执行测试
        if args.quick:
            success = runner.run_quick_tests()
        elif args.full:
            success = runner.run_full_tests()
        else:
            success = runner.run_all_tests(
                test_type=args.type,
                coverage=coverage,
                parallel=parallel
            )

        # 设置退出码
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试运行器异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()