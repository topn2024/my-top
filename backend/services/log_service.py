# -*- coding: utf-8 -*-
"""
日志服务层
提供日志查询、分析、统计的API服务

企业级日志分析功能:
- 智能错误分类（8大类，50+错误码）
- 错误趋势分析
- 性能监控统计
- 请求链路追踪
"""
import os
import re
import json
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from logger_config import setup_logger, log_service_call
from error_codes import (
    classify_error, get_all_categories, ErrorCategory, ErrorSeverity,
    EXCEPTION_TO_ERROR_CODE, KEYWORD_TO_ERROR_CODE
)

logger = setup_logger(__name__)

# 日志目录
LOG_DIR = Path(__file__).resolve().parent.parent.parent / 'logs'


class LogService:
    """日志服务类"""

    # 日志级别优先级
    LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

    # 日志行解析正则
    LOG_PATTERN = re.compile(
        r'^(\d{4}-\d{2}-\d{2}[\s,]\d{2}:\d{2}:\d{2}(?:,\d{3})?)\s*[-|]\s*'
        r'(\w+)\s*[-|]\s*(\w+(?:\.\w+)*)\s*[-|]\s*'
        r'(?:\[([^\]]+)\])?\s*[-|]?\s*(.*)$'
    )

    # 错误类型提取正则
    ERROR_TYPE_PATTERN = re.compile(r'([\w]+Error|[\w]+Exception)(?::|$)')

    # 性能日志解析正则 (格式: timestamp | request_id | operation | duration | message)
    PERF_PATTERN = re.compile(
        r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:,\d{3})?)\s*\|\s*'
        r'([^\|]+)\s*\|\s*'
        r'([^\|]+)\s*\|\s*'
        r'([\d.]+)s\s*\|\s*(.*)$'
    )

    def __init__(self, log_dir: str = None):
        self.log_dir = Path(log_dir) if log_dir else LOG_DIR

    def get_log_files(self) -> List[Dict[str, Any]]:
        """
        获取所有日志文件列表

        Returns:
            日志文件列表，包含名称、大小、行数、修改时间
        """
        files = []

        if not self.log_dir.exists():
            logger.warning(f"日志目录不存在: {self.log_dir}")
            return files

        for file_path in self.log_dir.glob('*.log*'):
            if file_path.is_file():
                stat = file_path.stat()
                # 计算行数
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        line_count = sum(1 for _ in f)
                except Exception:
                    line_count = 0

                files.append({
                    'name': file_path.name,
                    'size': stat.st_size,
                    'size_formatted': self._format_size(stat.st_size),
                    'lines': line_count,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })

        # 按修改时间排序
        files.sort(key=lambda x: x['modified'], reverse=True)
        return files

    def tail_logs(self, log_file: str = 'all.log', lines: int = 100,
                  offset: int = 0, level: str = None) -> Dict[str, Any]:
        """
        获取日志尾部内容

        Args:
            log_file: 日志文件名
            lines: 返回行数
            offset: 偏移量（用于分页）
            level: 日志级别过滤

        Returns:
            日志内容和元数据
        """
        log_path = self.log_dir / log_file

        if not log_path.exists():
            return {
                'logs': [],
                'total': 0,
                'has_more': False,
                'error': f'日志文件不存在: {log_file}'
            }

        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                all_lines = f.readlines()

            # 解析日志行
            parsed_logs = []
            for i, line in enumerate(all_lines):
                parsed = self._parse_log_line(line, i + 1)
                if parsed:
                    # 级别过滤
                    if level and level != 'ALL':
                        if parsed['level'] not in self._get_levels_from(level):
                            continue
                    parsed_logs.append(parsed)

            total = len(parsed_logs)

            # 从尾部取数据
            if offset > 0:
                end_idx = total - offset
                start_idx = max(0, end_idx - lines)
            else:
                start_idx = max(0, total - lines)
                end_idx = total

            result_logs = parsed_logs[start_idx:end_idx]

            return {
                'logs': result_logs,
                'total': total,
                'has_more': start_idx > 0,
                'offset': offset,
                'lines': lines
            }

        except Exception as e:
            logger.error(f"读取日志失败: {e}")
            return {
                'logs': [],
                'total': 0,
                'has_more': False,
                'error': str(e)
            }

    def search_logs(self, keyword: str, log_file: str = 'all.log',
                    level: str = None, start_time: str = None,
                    end_time: str = None, page: int = 1,
                    limit: int = 50, case_sensitive: bool = False) -> Dict[str, Any]:
        """
        搜索日志

        Args:
            keyword: 搜索关键词（支持正则）
            log_file: 日志文件名
            level: 日志级别过滤
            start_time: 开始时间 (ISO格式)
            end_time: 结束时间 (ISO格式)
            page: 页码
            limit: 每页数量
            case_sensitive: 是否区分大小写

        Returns:
            搜索结果
        """
        log_path = self.log_dir / log_file

        if not log_path.exists():
            return {
                'logs': [],
                'total': 0,
                'page': page,
                'pages': 0,
                'error': f'日志文件不存在: {log_file}'
            }

        try:
            # 编译搜索正则
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                search_pattern = re.compile(keyword, flags)
            except re.error:
                # 如果不是有效正则，转为普通字符串搜索
                search_pattern = re.compile(re.escape(keyword), flags)

            # 解析时间范围
            start_dt = datetime.fromisoformat(start_time) if start_time else None
            end_dt = datetime.fromisoformat(end_time) if end_time else None

            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                all_lines = f.readlines()

            # 搜索匹配
            matches = []
            for i, line in enumerate(all_lines):
                # 关键词匹配
                if not search_pattern.search(line):
                    continue

                parsed = self._parse_log_line(line, i + 1)
                if not parsed:
                    # 无法解析的行，作为原始内容
                    parsed = {
                        'line_number': i + 1,
                        'raw': line.strip(),
                        'level': 'UNKNOWN',
                        'timestamp': None
                    }

                # 级别过滤
                if level and level != 'ALL':
                    if parsed['level'] not in self._get_levels_from(level):
                        continue

                # 时间范围过滤
                if parsed.get('timestamp'):
                    log_dt = self._parse_timestamp(parsed['timestamp'])
                    if log_dt:
                        if start_dt and log_dt < start_dt:
                            continue
                        if end_dt and log_dt > end_dt:
                            continue

                matches.append(parsed)

            # 分页
            total = len(matches)
            pages = (total + limit - 1) // limit if limit > 0 else 1
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit

            return {
                'logs': matches[start_idx:end_idx],
                'total': total,
                'page': page,
                'pages': pages,
                'keyword': keyword
            }

        except Exception as e:
            logger.error(f"搜索日志失败: {e}")
            return {
                'logs': [],
                'total': 0,
                'page': page,
                'pages': 0,
                'error': str(e)
            }

    def search_by_request_id(self, request_id: str, log_file: str = 'all.log') -> Dict[str, Any]:
        """
        根据请求ID追踪完整请求链路

        Args:
            request_id: 请求ID
            log_file: 日志文件名

        Returns:
            请求链路日志
        """
        log_path = self.log_dir / log_file

        if not log_path.exists():
            return {
                'logs': [],
                'request_id': request_id,
                'error': f'日志文件不存在: {log_file}'
            }

        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                all_lines = f.readlines()

            matches = []
            for i, line in enumerate(all_lines):
                if request_id in line:
                    parsed = self._parse_log_line(line, i + 1)
                    if parsed:
                        matches.append(parsed)
                    else:
                        matches.append({
                            'line_number': i + 1,
                            'raw': line.strip(),
                            'level': 'UNKNOWN'
                        })

            return {
                'logs': matches,
                'request_id': request_id,
                'total': len(matches)
            }

        except Exception as e:
            logger.error(f"请求追踪失败: {e}")
            return {
                'logs': [],
                'request_id': request_id,
                'error': str(e)
            }

    def get_error_stats(self, hours: int = 24) -> Dict[str, Any]:
        """
        获取错误统计（企业级错误分类）

        Args:
            hours: 统计最近N小时

        Returns:
            错误统计数据，包含:
            - 按分类统计 (AUTH, BIZ, VALID, EXT, SYS, RES, NET, DB, UNK)
            - 按严重级别统计 (CRITICAL, ERROR, WARNING)
            - 错误趋势
            - 最近错误详情
        """
        log_path = self.log_dir / 'error.log'
        all_log_path = self.log_dir / 'all.log'

        # 优先使用error.log，如果不存在则从all.log提取
        if log_path.exists():
            target_path = log_path
        elif all_log_path.exists():
            target_path = all_log_path
        else:
            return self._empty_error_stats()

        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)

            # 统计容器
            by_category = Counter()      # 按分类
            by_severity = Counter()      # 按严重级别
            by_code = Counter()          # 按错误码
            by_hour = defaultdict(int)   # 按小时趋势
            recent_errors = []           # 最近错误

            with open(target_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    # 只处理ERROR级别
                    if 'ERROR' not in line and 'CRITICAL' not in line:
                        continue

                    parsed = self._parse_log_line(line)
                    if not parsed:
                        continue

                    # 时间过滤
                    log_dt = self._parse_timestamp(parsed.get('timestamp', ''))
                    if log_dt and log_dt < cutoff_time:
                        continue

                    # 提取异常类型
                    error_match = self.ERROR_TYPE_PATTERN.search(line)
                    exception_type = error_match.group(1) if error_match else None

                    # 使用企业级错误分类
                    error_info = classify_error(
                        parsed.get('message', ''),
                        exception_type
                    )

                    # 统计
                    by_category[error_info['category']] += 1
                    by_severity[error_info['severity']] += 1
                    by_code[error_info['code']] += 1

                    # 按小时统计
                    if log_dt:
                        hour_key = log_dt.strftime('%Y-%m-%d %H:00')
                        by_hour[hour_key] += 1

                    # 收集最近错误（带分类信息）
                    recent_errors.append({
                        'timestamp': parsed.get('timestamp'),
                        'code': error_info['code'],
                        'category': error_info['category'],
                        'category_name': error_info['category_name'],
                        'severity': error_info['severity'],
                        'name': error_info['name'],
                        'message': parsed.get('message', '')[:200],
                        'module': parsed.get('module'),
                        'solution': error_info.get('solution', '')
                    })

            # 生成趋势数据
            trend_labels = []
            trend_data = []
            current = datetime.now().replace(minute=0, second=0, microsecond=0)
            for i in range(min(24, hours)):
                hour = current - timedelta(hours=i)
                hour_key = hour.strftime('%Y-%m-%d %H:00')
                trend_labels.insert(0, hour.strftime('%H:00'))
                trend_data.insert(0, by_hour.get(hour_key, 0))

            # 分类统计详情
            category_stats = []
            for cat in ErrorCategory:
                count = by_category.get(cat.name, 0)
                if count > 0:
                    category_stats.append({
                        'category': cat.name,
                        'name': cat.name_cn,
                        'name_en': cat.name_en,
                        'count': count,
                        'percentage': round(count / sum(by_category.values()) * 100, 1) if by_category else 0
                    })

            # 严重级别统计
            severity_stats = {
                'CRITICAL': by_severity.get('CRITICAL', 0),
                'ERROR': by_severity.get('ERROR', 0),
                'WARNING': by_severity.get('WARNING', 0)
            }

            return {
                'total_errors': sum(by_category.values()),
                'by_category': category_stats,
                'by_severity': severity_stats,
                'by_code': dict(by_code.most_common(15)),
                'trend': {
                    'labels': trend_labels,
                    'data': trend_data
                },
                'recent': recent_errors[-30:][::-1],  # 最近30条，倒序
                'categories': get_all_categories()  # 所有分类定义
            }

        except Exception as e:
            logger.error(f"错误统计失败: {e}")
            return self._empty_error_stats(str(e))

    def _empty_error_stats(self, error: str = None) -> Dict[str, Any]:
        """返回空的错误统计结构"""
        result = {
            'total_errors': 0,
            'by_category': [],
            'by_severity': {'CRITICAL': 0, 'ERROR': 0, 'WARNING': 0},
            'by_code': {},
            'trend': {'labels': [], 'data': []},
            'recent': [],
            'categories': get_all_categories()
        }
        if error:
            result['error'] = error
        return result

    def get_performance_stats(self, hours: int = 24) -> Dict[str, Any]:
        """
        获取性能统计

        Args:
            hours: 统计最近N小时

        Returns:
            性能统计数据
        """
        perf_log = self.log_dir / 'performance.log'
        all_log = self.log_dir / 'all.log'

        operations = defaultdict(list)
        response_by_hour = defaultdict(list)
        cutoff_time = datetime.now() - timedelta(hours=hours)

        # 从performance.log读取
        if perf_log.exists():
            try:
                with open(perf_log, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        match = self.PERF_PATTERN.match(line)
                        if match:
                            timestamp, req_id, operation, duration, message = match.groups()
                            log_dt = self._parse_timestamp(timestamp)
                            if log_dt and log_dt >= cutoff_time:
                                duration = float(duration)
                                operations[operation.strip()].append(duration)
                                hour_key = log_dt.strftime('%H:00')
                                response_by_hour[hour_key].append(duration)
            except Exception as e:
                logger.warning(f"读取performance.log失败: {e}")

        # 从all.log提取带耗时的日志
        if all_log.exists():
            try:
                duration_pattern = re.compile(r'(\d+\.?\d*)s?\s*(?:秒|耗时|took|duration)', re.IGNORECASE)
                with open(all_log, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        if '完成' in line or 'took' in line.lower() or '耗时' in line:
                            parsed = self._parse_log_line(line)
                            if not parsed:
                                continue
                            log_dt = self._parse_timestamp(parsed.get('timestamp', ''))
                            if log_dt and log_dt >= cutoff_time:
                                # 提取耗时
                                dur_match = duration_pattern.search(line)
                                if dur_match:
                                    duration = float(dur_match.group(1))
                                    if duration < 300:  # 过滤异常值
                                        hour_key = log_dt.strftime('%H:00')
                                        response_by_hour[hour_key].append(duration)
            except Exception as e:
                logger.warning(f"读取all.log失败: {e}")

        # 计算统计数据
        all_durations = []
        for durations in operations.values():
            all_durations.extend(durations)
        for durations in response_by_hour.values():
            all_durations.extend(durations)

        # 去重
        all_durations = list(set(all_durations)) if all_durations else [0]

        total_requests = len(all_durations)
        avg_time = sum(all_durations) / len(all_durations) if all_durations else 0
        sorted_durations = sorted(all_durations)
        p95_time = sorted_durations[int(len(sorted_durations) * 0.95)] if len(sorted_durations) > 1 else 0
        p99_time = sorted_durations[int(len(sorted_durations) * 0.99)] if len(sorted_durations) > 1 else 0
        slow_requests = sum(1 for d in all_durations if d > 2.0)

        # 端点性能统计
        endpoint_stats = []
        for endpoint, durations in sorted(operations.items(), key=lambda x: sum(x[1])/len(x[1]) if x[1] else 0, reverse=True)[:10]:
            if durations:
                sorted_d = sorted(durations)
                endpoint_stats.append({
                    'endpoint': endpoint,
                    'count': len(durations),
                    'avg': round(sum(durations) / len(durations), 3),
                    'min': round(min(durations), 3),
                    'max': round(max(durations), 3),
                    'p95': round(sorted_d[int(len(sorted_d) * 0.95)] if len(sorted_d) > 1 else sorted_d[0], 3)
                })

        # 趋势数据
        trend_labels = []
        trend_data = []
        current = datetime.now().replace(minute=0, second=0, microsecond=0)
        for i in range(min(24, hours)):
            hour = current - timedelta(hours=i)
            hour_key = hour.strftime('%H:00')
            trend_labels.insert(0, hour_key)
            hour_durations = response_by_hour.get(hour_key, [])
            avg = sum(hour_durations) / len(hour_durations) if hour_durations else 0
            trend_data.insert(0, round(avg, 3))

        return {
            'total_requests': total_requests,
            'avg_response_time': round(avg_time, 3),
            'p95_response_time': round(p95_time, 3),
            'p99_response_time': round(p99_time, 3),
            'slow_requests': slow_requests,
            'by_endpoint': endpoint_stats,
            'trend': {
                'labels': trend_labels,
                'avg_times': trend_data
            }
        }

    def get_slow_queries(self, hours: int = 24) -> Dict[str, Any]:
        """
        获取慢查询统计

        Args:
            hours: 统计最近N小时

        Returns:
            慢查询统计数据
        """
        slow_log = self.log_dir / 'slow.log'
        all_log = self.log_dir / 'all.log'

        slow_queries = []
        cutoff_time = datetime.now() - timedelta(hours=hours)

        # 慢查询正则
        slow_pattern = re.compile(r'SLOW\s+(API|QUERY|SERVICE):\s*(.+?)\s+took\s+([\d.]+)s')

        # 从slow.log读取
        if slow_log.exists():
            try:
                with open(slow_log, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        match = slow_pattern.search(line)
                        if match:
                            query_type, operation, duration = match.groups()
                            parsed = self._parse_log_line(line)
                            log_dt = self._parse_timestamp(parsed.get('timestamp', '')) if parsed else None

                            if not log_dt or log_dt >= cutoff_time:
                                slow_queries.append({
                                    'type': query_type,
                                    'operation': operation.strip(),
                                    'duration': float(duration),
                                    'timestamp': parsed.get('timestamp') if parsed else None
                                })
            except Exception as e:
                logger.warning(f"读取slow.log失败: {e}")

        # 从all.log补充
        if all_log.exists():
            try:
                with open(all_log, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        if 'SLOW' in line:
                            match = slow_pattern.search(line)
                            if match:
                                query_type, operation, duration = match.groups()
                                parsed = self._parse_log_line(line)
                                log_dt = self._parse_timestamp(parsed.get('timestamp', '')) if parsed else None

                                if not log_dt or log_dt >= cutoff_time:
                                    slow_queries.append({
                                        'type': query_type,
                                        'operation': operation.strip(),
                                        'duration': float(duration),
                                        'timestamp': parsed.get('timestamp') if parsed else None
                                    })
            except Exception as e:
                logger.warning(f"读取all.log失败: {e}")

        # 按类型分组
        by_type = defaultdict(list)
        for query in slow_queries:
            by_type[query['type']].append(query)

        # 排序
        for query_type in by_type:
            by_type[query_type].sort(key=lambda x: x['duration'], reverse=True)

        return {
            'total': len(slow_queries),
            'by_type': {
                k: {
                    'count': len(v),
                    'queries': v[:10]  # 每种类型最多10条
                }
                for k, v in by_type.items()
            },
            'top_slow': sorted(slow_queries, key=lambda x: x['duration'], reverse=True)[:20]
        }

    def export_logs(self, log_file: str = 'all.log', start_time: str = None,
                    end_time: str = None, level: str = None,
                    format: str = 'txt') -> Tuple[str, str]:
        """
        导出日志

        Args:
            log_file: 日志文件名
            start_time: 开始时间
            end_time: 结束时间
            level: 日志级别
            format: 导出格式 (txt/json)

        Returns:
            (导出内容, 文件名)
        """
        log_path = self.log_dir / log_file

        if not log_path.exists():
            raise FileNotFoundError(f"日志文件不存在: {log_file}")

        # 解析时间范围
        start_dt = datetime.fromisoformat(start_time) if start_time else None
        end_dt = datetime.fromisoformat(end_time) if end_time else None

        logs = []
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                parsed = self._parse_log_line(line)

                # 级别过滤
                if level and level != 'ALL':
                    if not parsed or parsed['level'] not in self._get_levels_from(level):
                        continue

                # 时间过滤
                if parsed and parsed.get('timestamp'):
                    log_dt = self._parse_timestamp(parsed['timestamp'])
                    if log_dt:
                        if start_dt and log_dt < start_dt:
                            continue
                        if end_dt and log_dt > end_dt:
                            continue

                if format == 'json':
                    logs.append(parsed or {'raw': line.strip()})
                else:
                    logs.append(line.rstrip())

        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"logs_export_{timestamp}.{format}"

        if format == 'json':
            content = json.dumps(logs, ensure_ascii=False, indent=2)
        else:
            content = '\n'.join(logs)

        return content, filename

    def _parse_log_line(self, line: str, line_number: int = None) -> Optional[Dict[str, Any]]:
        """解析日志行"""
        line = line.strip()
        if not line:
            return None

        match = self.LOG_PATTERN.match(line)
        if match:
            timestamp, level, module, location, message = match.groups()
            return {
                'line_number': line_number,
                'timestamp': timestamp,
                'level': level.upper(),
                'module': module,
                'location': location,
                'message': message.strip(),
                'raw': line
            }

        # 尝试简单格式匹配
        simple_match = re.match(
            r'^(\d{4}-\d{2}-\d{2}[\s,]\d{2}:\d{2}:\d{2}(?:,\d{3})?)\s*-\s*'
            r'(\S+)\s*-\s*(\w+)\s*-\s*(.*)$',
            line
        )
        if simple_match:
            timestamp, module, level, message = simple_match.groups()
            return {
                'line_number': line_number,
                'timestamp': timestamp,
                'level': level.upper(),
                'module': module,
                'message': message.strip(),
                'raw': line
            }

        return None

    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """解析时间戳"""
        if not timestamp_str:
            return None

        formats = [
            '%Y-%m-%d %H:%M:%S,%f',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d,%H:%M:%S,%f',
            '%Y-%m-%d,%H:%M:%S'
        ]

        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str.strip(), fmt)
            except ValueError:
                continue

        return None

    def _get_levels_from(self, level: str) -> List[str]:
        """获取指定级别及以上的所有级别"""
        level = level.upper()
        if level not in self.LOG_LEVELS:
            return self.LOG_LEVELS
        idx = self.LOG_LEVELS.index(level)
        return self.LOG_LEVELS[idx:]

    @staticmethod
    def _format_size(size: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


# 单例实例
_log_service = None


def get_log_service() -> LogService:
    """获取日志服务单例"""
    global _log_service
    if _log_service is None:
        _log_service = LogService()
    return _log_service
