#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志分析工具
提供日志查询、分析、统计功能
"""
import os
import sys
import re
import argparse
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import json

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')


class LogAnalyzer:
    """日志分析器"""

    def __init__(self, log_dir=LOG_DIR):
        self.log_dir = log_dir

    def tail_logs(self, log_file='all.log', lines=50, follow=False):
        """
        查看日志尾部

        Args:
            log_file: 日志文件名
            lines: 显示行数
            follow: 是否实时跟踪
        """
        log_path = os.path.join(self.log_dir, log_file)

        if not os.path.exists(log_path):
            print(f"❌ 日志文件不存在: {log_path}")
            return

        if follow:
            # 实时跟踪日志
            import subprocess
            if sys.platform == 'win32':
                # Windows使用PowerShell
                cmd = f'powershell Get-Content -Path "{log_path}" -Wait -Tail {lines}'
            else:
                # Linux/Mac使用tail -f
                cmd = f'tail -f -n {lines} "{log_path}"'

            try:
                subprocess.run(cmd, shell=True)
            except KeyboardInterrupt:
                print("\n已停止跟踪日志")
        else:
            # 显示最后N行
            try:
                with open(log_path, 'r', encoding='utf-8') as f:
                    all_lines = f.readlines()
                    last_lines = all_lines[-lines:]
                    print(f"\n{'=' * 100}")
                    print(f"📄 {log_file} - 最后 {lines} 行")
                    print(f"{'=' * 100}\n")
                    for line in last_lines:
                        print(line.rstrip())
            except Exception as e:
                print(f"❌ 读取日志失败: {e}")

    def search_logs(self, keyword, log_file='all.log', case_sensitive=False, context=0):
        """
        搜索日志内容

        Args:
            keyword: 搜索关键词
            log_file: 日志文件名
            case_sensitive: 是否区分大小写
            context: 显示上下文行数
        """
        log_path = os.path.join(self.log_dir, log_file)

        if not os.path.exists(log_path):
            print(f"❌ 日志文件不存在: {log_path}")
            return

        print(f"\n{'=' * 100}")
        print(f"🔍 搜索关键词: '{keyword}' (文件: {log_file})")
        print(f"{'=' * 100}\n")

        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            matches = []
            for i, line in enumerate(lines):
                search_line = line if case_sensitive else line.lower()
                search_keyword = keyword if case_sensitive else keyword.lower()

                if search_keyword in search_line:
                    matches.append((i, line))

            if matches:
                print(f"✓ 找到 {len(matches)} 处匹配:\n")
                for line_num, line in matches:
                    # 显示上下文
                    if context > 0:
                        start = max(0, line_num - context)
                        end = min(len(lines), line_num + context + 1)
                        print(f"--- 行 {line_num + 1} ---")
                        for i in range(start, end):
                            marker = ">>> " if i == line_num else "    "
                            print(f"{marker}{lines[i].rstrip()}")
                        print()
                    else:
                        print(f"行 {line_num + 1}: {line.rstrip()}")
            else:
                print("❌ 未找到匹配项")

        except Exception as e:
            print(f"❌ 搜索失败: {e}")

    def search_by_request_id(self, request_id, log_file='all.log'):
        """
        根据请求ID搜索完整请求链路

        Args:
            request_id: 请求ID
            log_file: 日志文件名
        """
        log_path = os.path.join(self.log_dir, log_file)

        if not os.path.exists(log_path):
            print(f"❌ 日志文件不存在: {log_path}")
            return

        print(f"\n{'=' * 100}")
        print(f"🔗 追踪请求: {request_id}")
        print(f"{'=' * 100}\n")

        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            matches = []
            for i, line in enumerate(lines):
                if request_id in line:
                    matches.append((i, line))

            if matches:
                print(f"✓ 找到 {len(matches)} 条相关日志:\n")
                for line_num, line in matches:
                    print(line.rstrip())
            else:
                print(f"❌ 未找到请求ID: {request_id}")

        except Exception as e:
            print(f"❌ 搜索失败: {e}")

    def analyze_errors(self, log_file='error.log', hours=24):
        """
        分析错误日志

        Args:
            log_file: 日志文件名
            hours: 分析最近N小时的日志
        """
        log_path = os.path.join(self.log_dir, log_file)

        if not os.path.exists(log_path):
            print(f"❌ 日志文件不存在: {log_path}")
            return

        print(f"\n{'=' * 100}")
        print(f"📊 错误日志分析 - 最近 {hours} 小时")
        print(f"{'=' * 100}\n")

        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            error_types = Counter()
            error_details = []

            with open(log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    # 解析时间戳
                    match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                    if match:
                        log_time_str = match.group(1)
                        try:
                            log_time = datetime.strptime(log_time_str, '%Y-%m-%d %H:%M:%S')
                            if log_time < cutoff_time:
                                continue
                        except:
                            pass

                    # 提取错误类型
                    if 'ERROR' in line:
                        # 尝试提取异常类型
                        exc_match = re.search(r'([\w]+Error|[\w]+Exception):', line)
                        if exc_match:
                            error_type = exc_match.group(1)
                            error_types[error_type] += 1
                            error_details.append({
                                'type': error_type,
                                'message': line.strip()[:200]
                            })

            # 显示统计
            print(f"错误总数: {sum(error_types.values())}\n")

            if error_types:
                print("错误类型分布:")
                for error_type, count in error_types.most_common(10):
                    percentage = (count / sum(error_types.values())) * 100
                    bar = '█' * int(percentage / 2)
                    print(f"  {error_type:30} | {count:4} | {percentage:5.1f}% {bar}")

                print(f"\n最近的错误:")
                for detail in error_details[-5:]:
                    print(f"  [{detail['type']}] {detail['message']}")
            else:
                print("✓ 最近没有错误")

        except Exception as e:
            print(f"❌ 分析失败: {e}")

    def analyze_performance(self, log_file='performance.log', hours=24):
        """
        分析性能日志

        Args:
            log_file: 日志文件名
            hours: 分析最近N小时的日志
        """
        log_path = os.path.join(self.log_dir, log_file)

        if not os.path.exists(log_path):
            print(f"⚠️  性能日志文件不存在: {log_path}")
            print("   性能日志需要在使用增强版logger_config后才会生成")
            return

        print(f"\n{'=' * 100}")
        print(f"⚡ 性能分析 - 最近 {hours} 小时")
        print(f"{'=' * 100}\n")

        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            operations = defaultdict(list)

            with open(log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    # 解析时间戳
                    match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                    if match:
                        log_time_str = match.group(1)
                        try:
                            log_time = datetime.strptime(log_time_str, '%Y-%m-%d %H:%M:%S')
                            if log_time < cutoff_time:
                                continue
                        except:
                            pass

                    # 解析操作和耗时
                    # 格式: timestamp | request_id | operation | duration | message
                    parts = line.split('|')
                    if len(parts) >= 4:
                        operation = parts[2].strip()
                        duration_str = parts[3].strip()
                        # 提取数字
                        duration_match = re.search(r'([\d.]+)s', duration_str)
                        if duration_match:
                            duration = float(duration_match.group(1))
                            operations[operation].append(duration)

            if operations:
                print(f"总请求数: {sum(len(v) for v in operations.values())}\n")
                print("操作性能统计:")
                print(f"{'操作':40} | {'次数':6} | {'平均':8} | {'最小':8} | {'最大':8} | {'P95':8}")
                print("-" * 100)

                for operation, durations in sorted(operations.items(), key=lambda x: sum(x[1])/len(x[1]), reverse=True)[:20]:
                    count = len(durations)
                    avg = sum(durations) / count
                    min_time = min(durations)
                    max_time = max(durations)
                    sorted_durations = sorted(durations)
                    p95 = sorted_durations[int(len(sorted_durations) * 0.95)] if count > 1 else durations[0]

                    print(f"{operation[:40]:40} | {count:6} | {avg:7.3f}s | {min_time:7.3f}s | {max_time:7.3f}s | {p95:7.3f}s")
            else:
                print("⚠️  没有性能数据")

        except Exception as e:
            print(f"❌ 分析失败: {e}")

    def analyze_slow_queries(self, log_file='slow.log'):
        """
        分析慢查询日志

        Args:
            log_file: 日志文件名
        """
        log_path = os.path.join(self.log_dir, log_file)

        if not os.path.exists(log_path):
            print(f"⚠️  慢查询日志文件不存在: {log_path}")
            print("   慢查询日志需要在使用增强版logger_config后才会生成")
            return

        print(f"\n{'=' * 100}")
        print(f"🐌 慢查询分析")
        print(f"{'=' * 100}\n")

        try:
            slow_queries = []

            with open(log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    # 解析慢查询信息
                    if 'SLOW' in line:
                        # 提取操作名和耗时
                        match = re.search(r'SLOW (API|QUERY|SERVICE): (.+?) took ([\d.]+)s', line)
                        if match:
                            query_type = match.group(1)
                            operation = match.group(2)
                            duration = float(match.group(3))
                            slow_queries.append({
                                'type': query_type,
                                'operation': operation,
                                'duration': duration,
                                'line': line.strip()
                            })

            if slow_queries:
                print(f"慢查询总数: {len(slow_queries)}\n")

                # 按类型分组
                by_type = defaultdict(list)
                for query in slow_queries:
                    by_type[query['type']].append(query)

                for query_type, queries in by_type.items():
                    print(f"\n{query_type} 类型慢查询 ({len(queries)} 个):")
                    print("-" * 100)
                    for query in sorted(queries, key=lambda x: x['duration'], reverse=True)[:10]:
                        print(f"  {query['duration']:6.2f}s | {query['operation']}")
            else:
                print("✓ 没有慢查询")

        except Exception as e:
            print(f"❌ 分析失败: {e}")

    def list_log_files(self):
        """列出所有日志文件"""
        print(f"\n{'=' * 100}")
        print(f"📁 日志文件列表 ({self.log_dir})")
        print(f"{'=' * 100}\n")

        try:
            if not os.path.exists(self.log_dir):
                print(f"❌ 日志目录不存在: {self.log_dir}")
                return

            log_files = []
            for file in os.listdir(self.log_dir):
                if file.endswith('.log'):
                    file_path = os.path.join(self.log_dir, file)
                    size = os.path.getsize(file_path)
                    mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    log_files.append((file, size, mtime))

            if log_files:
                print(f"{'文件名':30} | {'大小':12} | {'最后修改时间':20}")
                print("-" * 100)
                for file, size, mtime in sorted(log_files, key=lambda x: x[2], reverse=True):
                    size_str = self._format_size(size)
                    mtime_str = mtime.strftime('%Y-%m-%d %H:%M:%S')
                    print(f"{file:30} | {size_str:12} | {mtime_str:20}")
            else:
                print("❌ 没有日志文件")

        except Exception as e:
            print(f"❌ 列出文件失败: {e}")

    @staticmethod
    def _format_size(size):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='TOP_N 日志分析工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 查看最后50行日志
  python log_analyzer.py --tail

  # 实时跟踪日志
  python log_analyzer.py --tail --follow

  # 搜索关键词
  python log_analyzer.py --search "ERROR"

  # 根据请求ID追踪
  python log_analyzer.py --request-id abc12345

  # 分析错误
  python log_analyzer.py --analyze-errors

  # 分析性能
  python log_analyzer.py --analyze-performance

  # 列出所有日志文件
  python log_analyzer.py --list
        """
    )

    parser.add_argument('--tail', action='store_true', help='查看日志尾部')
    parser.add_argument('--follow', '-f', action='store_true', help='实时跟踪日志')
    parser.add_argument('--lines', '-n', type=int, default=50, help='显示行数（默认50）')
    parser.add_argument('--search', '-s', metavar='KEYWORD', help='搜索关键词')
    parser.add_argument('--request-id', '-r', metavar='ID', help='根据请求ID追踪')
    parser.add_argument('--analyze-errors', '-e', action='store_true', help='分析错误日志')
    parser.add_argument('--analyze-performance', '-p', action='store_true', help='分析性能日志')
    parser.add_argument('--analyze-slow', action='store_true', help='分析慢查询日志')
    parser.add_argument('--list', '-l', action='store_true', help='列出所有日志文件')
    parser.add_argument('--log-file', default='all.log', help='指定日志文件（默认all.log）')
    parser.add_argument('--hours', type=int, default=24, help='分析最近N小时（默认24）')
    parser.add_argument('--context', '-C', type=int, default=0, help='显示上下文行数')

    args = parser.parse_args()

    analyzer = LogAnalyzer()

    # 执行操作
    if args.list:
        analyzer.list_log_files()
    elif args.tail:
        analyzer.tail_logs(args.log_file, args.lines, args.follow)
    elif args.search:
        analyzer.search_logs(args.search, args.log_file, context=args.context)
    elif args.request_id:
        analyzer.search_by_request_id(args.request_id, args.log_file)
    elif args.analyze_errors:
        analyzer.analyze_errors('error.log', args.hours)
    elif args.analyze_performance:
        analyzer.analyze_performance('performance.log', args.hours)
    elif args.analyze_slow:
        analyzer.analyze_slow_queries('slow.log')
    else:
        # 默认显示帮助
        parser.print_help()


if __name__ == '__main__':
    main()
