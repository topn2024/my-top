#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业级错误码定义模块

错误码规范:
- 格式: ERR-CNNNN (C=分类, NNNN=序号)
- 分类前缀:
  - 1xxxx: AUTH  - 认证授权类
  - 2xxxx: BIZ   - 业务逻辑类
  - 3xxxx: VALID - 数据验证类
  - 4xxxx: EXT   - 外部服务类
  - 5xxxx: SYS   - 系统内部类
  - 6xxxx: RES   - 资源类
  - 7xxxx: NET   - 网络类
  - 8xxxx: DB    - 数据库类
  - 9xxxx: UNK   - 未知/其他

严重级别:
- CRITICAL: 系统级严重错误，需立即处理
- ERROR: 业务级错误，影响单个请求
- WARNING: 警告，可能导致问题
"""
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional, List
import re


class ErrorSeverity(Enum):
    """错误严重级别"""
    CRITICAL = "CRITICAL"  # 系统崩溃、数据损坏
    ERROR = "ERROR"        # 请求失败、业务异常
    WARNING = "WARNING"    # 潜在问题、降级服务


class ErrorCategory(Enum):
    """错误分类"""
    AUTH = ("1", "认证授权", "Authentication & Authorization")
    BIZ = ("2", "业务逻辑", "Business Logic")
    VALID = ("3", "数据验证", "Data Validation")
    EXT = ("4", "外部服务", "External Service")
    SYS = ("5", "系统内部", "System Internal")
    RES = ("6", "资源管理", "Resource Management")
    NET = ("7", "网络通信", "Network Communication")
    DB = ("8", "数据库", "Database")
    UNK = ("9", "未知错误", "Unknown")

    def __init__(self, code_prefix: str, name_cn: str, name_en: str):
        self.code_prefix = code_prefix
        self.name_cn = name_cn
        self.name_en = name_en


@dataclass
class ErrorDefinition:
    """错误定义"""
    code: str
    category: ErrorCategory
    severity: ErrorSeverity
    name: str
    description: str
    solution: str = ""

    @property
    def full_code(self) -> str:
        return f"ERR-{self.code}"


# ============================================================
# 错误码定义
# ============================================================

ERROR_DEFINITIONS: Dict[str, ErrorDefinition] = {}


def define_error(code: str, category: ErrorCategory, severity: ErrorSeverity,
                 name: str, description: str, solution: str = "") -> ErrorDefinition:
    """注册错误定义"""
    error_def = ErrorDefinition(code, category, severity, name, description, solution)
    ERROR_DEFINITIONS[code] = error_def
    return error_def


# ============================================================
# 1xxxx - 认证授权类错误
# ============================================================

AUTH_LOGIN_FAILED = define_error(
    "10001", ErrorCategory.AUTH, ErrorSeverity.WARNING,
    "登录失败", "用户名或密码错误",
    "请检查用户名和密码是否正确"
)

AUTH_TOKEN_EXPIRED = define_error(
    "10002", ErrorCategory.AUTH, ErrorSeverity.WARNING,
    "令牌过期", "访问令牌已过期，需要重新登录",
    "请重新登录获取新的访问令牌"
)

AUTH_TOKEN_INVALID = define_error(
    "10003", ErrorCategory.AUTH, ErrorSeverity.WARNING,
    "令牌无效", "访问令牌格式错误或已被篡改",
    "请重新登录"
)

AUTH_PERMISSION_DENIED = define_error(
    "10004", ErrorCategory.AUTH, ErrorSeverity.WARNING,
    "权限不足", "用户没有执行此操作的权限",
    "请联系管理员获取相应权限"
)

AUTH_SESSION_EXPIRED = define_error(
    "10005", ErrorCategory.AUTH, ErrorSeverity.WARNING,
    "会话过期", "用户会话已过期",
    "请重新登录"
)

AUTH_ACCOUNT_LOCKED = define_error(
    "10006", ErrorCategory.AUTH, ErrorSeverity.WARNING,
    "账户锁定", "账户因多次登录失败被锁定",
    "请等待30分钟后重试或联系管理员"
)

AUTH_ACCOUNT_DISABLED = define_error(
    "10007", ErrorCategory.AUTH, ErrorSeverity.WARNING,
    "账户禁用", "账户已被管理员禁用",
    "请联系管理员"
)

AUTH_PLATFORM_LOGIN_FAILED = define_error(
    "10101", ErrorCategory.AUTH, ErrorSeverity.ERROR,
    "平台登录失败", "第三方平台登录失败",
    "请检查账号状态或重新扫码登录"
)

AUTH_COOKIE_EXPIRED = define_error(
    "10102", ErrorCategory.AUTH, ErrorSeverity.WARNING,
    "Cookie过期", "平台登录Cookie已过期",
    "请重新登录平台"
)

AUTH_QR_CODE_EXPIRED = define_error(
    "10103", ErrorCategory.AUTH, ErrorSeverity.WARNING,
    "二维码过期", "登录二维码已过期",
    "请刷新二维码重新扫描"
)

# ============================================================
# 2xxxx - 业务逻辑类错误
# ============================================================

BIZ_ARTICLE_NOT_FOUND = define_error(
    "20001", ErrorCategory.BIZ, ErrorSeverity.WARNING,
    "文章不存在", "请求的文章不存在或已被删除",
    "请检查文章ID是否正确"
)

BIZ_WORKFLOW_FAILED = define_error(
    "20002", ErrorCategory.BIZ, ErrorSeverity.ERROR,
    "工作流失败", "自动化工作流执行失败",
    "请检查工作流配置和日志"
)

BIZ_PUBLISH_FAILED = define_error(
    "20003", ErrorCategory.BIZ, ErrorSeverity.ERROR,
    "发布失败", "文章发布到平台失败",
    "请检查平台登录状态和网络连接"
)

BIZ_CONTENT_GENERATE_FAILED = define_error(
    "20004", ErrorCategory.BIZ, ErrorSeverity.ERROR,
    "内容生成失败", "AI内容生成失败",
    "请检查API配额和网络连接"
)

BIZ_DUPLICATE_CONTENT = define_error(
    "20005", ErrorCategory.BIZ, ErrorSeverity.WARNING,
    "内容重复", "检测到重复内容",
    "请修改内容后重试"
)

BIZ_CONTENT_TOO_LONG = define_error(
    "20006", ErrorCategory.BIZ, ErrorSeverity.WARNING,
    "内容超长", "文章内容超过平台限制",
    "请缩短文章内容"
)

BIZ_RATE_LIMIT_EXCEEDED = define_error(
    "20007", ErrorCategory.BIZ, ErrorSeverity.WARNING,
    "频率限制", "操作过于频繁，触发频率限制",
    "请稍后重试"
)

BIZ_TASK_QUEUE_FULL = define_error(
    "20008", ErrorCategory.BIZ, ErrorSeverity.WARNING,
    "任务队列满", "后台任务队列已满",
    "请等待当前任务完成后重试"
)

BIZ_ANALYSIS_FAILED = define_error(
    "20009", ErrorCategory.BIZ, ErrorSeverity.ERROR,
    "分析失败", "内容分析过程失败",
    "请检查输入内容格式"
)

# ============================================================
# 3xxxx - 数据验证类错误
# ============================================================

VALID_PARAM_MISSING = define_error(
    "30001", ErrorCategory.VALID, ErrorSeverity.WARNING,
    "参数缺失", "必需的请求参数未提供",
    "请检查API文档，提供所有必需参数"
)

VALID_PARAM_INVALID = define_error(
    "30002", ErrorCategory.VALID, ErrorSeverity.WARNING,
    "参数无效", "请求参数格式或值无效",
    "请检查参数格式是否符合要求"
)

VALID_JSON_PARSE_ERROR = define_error(
    "30003", ErrorCategory.VALID, ErrorSeverity.WARNING,
    "JSON解析错误", "请求体JSON格式错误",
    "请检查JSON格式是否正确"
)

VALID_URL_INVALID = define_error(
    "30004", ErrorCategory.VALID, ErrorSeverity.WARNING,
    "URL无效", "提供的URL格式无效",
    "请检查URL格式"
)

VALID_FILE_TYPE_ERROR = define_error(
    "30005", ErrorCategory.VALID, ErrorSeverity.WARNING,
    "文件类型错误", "上传的文件类型不支持",
    "请上传支持的文件格式"
)

VALID_FILE_SIZE_EXCEEDED = define_error(
    "30006", ErrorCategory.VALID, ErrorSeverity.WARNING,
    "文件过大", "上传的文件超过大小限制",
    "请压缩文件或分批上传"
)

VALID_EMAIL_INVALID = define_error(
    "30007", ErrorCategory.VALID, ErrorSeverity.WARNING,
    "邮箱格式错误", "邮箱地址格式无效",
    "请输入正确的邮箱地址"
)

VALID_DATA_FORMAT_ERROR = define_error(
    "30008", ErrorCategory.VALID, ErrorSeverity.WARNING,
    "数据格式错误", "数据格式不符合要求",
    "请检查数据格式"
)

# ============================================================
# 4xxxx - 外部服务类错误
# ============================================================

EXT_API_ERROR = define_error(
    "40001", ErrorCategory.EXT, ErrorSeverity.ERROR,
    "外部API错误", "调用第三方API时发生错误",
    "请检查API状态和配置"
)

EXT_API_TIMEOUT = define_error(
    "40002", ErrorCategory.EXT, ErrorSeverity.ERROR,
    "API超时", "第三方API响应超时",
    "请稍后重试"
)

EXT_API_RATE_LIMITED = define_error(
    "40003", ErrorCategory.EXT, ErrorSeverity.WARNING,
    "API限流", "第三方API触发限流",
    "请降低请求频率或升级配额"
)

EXT_API_QUOTA_EXCEEDED = define_error(
    "40004", ErrorCategory.EXT, ErrorSeverity.ERROR,
    "配额耗尽", "第三方API配额已用完",
    "请充值或等待配额重置"
)

EXT_PLATFORM_ERROR = define_error(
    "40101", ErrorCategory.EXT, ErrorSeverity.ERROR,
    "平台错误", "发布平台返回错误",
    "请检查平台状态"
)

EXT_PLATFORM_UNAVAILABLE = define_error(
    "40102", ErrorCategory.EXT, ErrorSeverity.ERROR,
    "平台不可用", "发布平台暂时不可用",
    "请稍后重试"
)

EXT_OPENAI_ERROR = define_error(
    "40201", ErrorCategory.EXT, ErrorSeverity.ERROR,
    "OpenAI错误", "OpenAI API调用失败",
    "请检查API密钥和配额"
)

EXT_CAPTCHA_SERVICE_ERROR = define_error(
    "40301", ErrorCategory.EXT, ErrorSeverity.ERROR,
    "验证码服务错误", "验证码识别服务失败",
    "请检查验证码服务配置"
)

# ============================================================
# 5xxxx - 系统内部类错误
# ============================================================

SYS_INTERNAL_ERROR = define_error(
    "50001", ErrorCategory.SYS, ErrorSeverity.CRITICAL,
    "系统内部错误", "系统发生未预期的内部错误",
    "请联系技术支持"
)

SYS_CONFIG_ERROR = define_error(
    "50002", ErrorCategory.SYS, ErrorSeverity.CRITICAL,
    "配置错误", "系统配置错误",
    "请检查系统配置文件"
)

SYS_MODULE_LOAD_ERROR = define_error(
    "50003", ErrorCategory.SYS, ErrorSeverity.CRITICAL,
    "模块加载失败", "系统模块加载失败",
    "请检查模块依赖是否完整"
)

SYS_MEMORY_ERROR = define_error(
    "50004", ErrorCategory.SYS, ErrorSeverity.CRITICAL,
    "内存不足", "系统内存不足",
    "请增加服务器内存或优化程序"
)

SYS_DISK_FULL = define_error(
    "50005", ErrorCategory.SYS, ErrorSeverity.CRITICAL,
    "磁盘空间不足", "服务器磁盘空间不足",
    "请清理磁盘空间"
)

SYS_PROCESS_ERROR = define_error(
    "50006", ErrorCategory.SYS, ErrorSeverity.ERROR,
    "进程错误", "后台进程执行错误",
    "请检查进程日志"
)

SYS_SCHEDULER_ERROR = define_error(
    "50007", ErrorCategory.SYS, ErrorSeverity.ERROR,
    "调度器错误", "任务调度器错误",
    "请检查调度器配置"
)

SYS_CACHE_ERROR = define_error(
    "50008", ErrorCategory.SYS, ErrorSeverity.WARNING,
    "缓存错误", "缓存服务错误",
    "请检查Redis连接"
)

# ============================================================
# 6xxxx - 资源类错误
# ============================================================

RES_NOT_FOUND = define_error(
    "60001", ErrorCategory.RES, ErrorSeverity.WARNING,
    "资源不存在", "请求的资源不存在",
    "请检查资源ID是否正确"
)

RES_FILE_NOT_FOUND = define_error(
    "60002", ErrorCategory.RES, ErrorSeverity.WARNING,
    "文件不存在", "请求的文件不存在",
    "请检查文件路径"
)

RES_ALREADY_EXISTS = define_error(
    "60003", ErrorCategory.RES, ErrorSeverity.WARNING,
    "资源已存在", "尝试创建的资源已存在",
    "请使用不同的标识符"
)

RES_LOCKED = define_error(
    "60004", ErrorCategory.RES, ErrorSeverity.WARNING,
    "资源被锁定", "资源正在被其他操作使用",
    "请稍后重试"
)

RES_DELETED = define_error(
    "60005", ErrorCategory.RES, ErrorSeverity.WARNING,
    "资源已删除", "资源已被删除",
    "无法对已删除的资源进行操作"
)

# ============================================================
# 7xxxx - 网络类错误
# ============================================================

NET_CONNECTION_ERROR = define_error(
    "70001", ErrorCategory.NET, ErrorSeverity.ERROR,
    "网络连接错误", "无法建立网络连接",
    "请检查网络连接"
)

NET_TIMEOUT = define_error(
    "70002", ErrorCategory.NET, ErrorSeverity.ERROR,
    "网络超时", "网络请求超时",
    "请检查网络状况或稍后重试"
)

NET_DNS_ERROR = define_error(
    "70003", ErrorCategory.NET, ErrorSeverity.ERROR,
    "DNS解析失败", "域名解析失败",
    "请检查DNS设置"
)

NET_SSL_ERROR = define_error(
    "70004", ErrorCategory.NET, ErrorSeverity.ERROR,
    "SSL证书错误", "SSL/TLS证书验证失败",
    "请检查证书配置"
)

NET_PROXY_ERROR = define_error(
    "70005", ErrorCategory.NET, ErrorSeverity.ERROR,
    "代理错误", "代理服务器连接失败",
    "请检查代理配置"
)

# ============================================================
# 8xxxx - 数据库类错误
# ============================================================

DB_CONNECTION_ERROR = define_error(
    "80001", ErrorCategory.DB, ErrorSeverity.CRITICAL,
    "数据库连接失败", "无法连接到数据库",
    "请检查数据库服务状态"
)

DB_QUERY_ERROR = define_error(
    "80002", ErrorCategory.DB, ErrorSeverity.ERROR,
    "数据库查询错误", "SQL查询执行失败",
    "请检查SQL语句"
)

DB_TRANSACTION_ERROR = define_error(
    "80003", ErrorCategory.DB, ErrorSeverity.ERROR,
    "事务错误", "数据库事务执行失败",
    "请检查事务逻辑"
)

DB_INTEGRITY_ERROR = define_error(
    "80004", ErrorCategory.DB, ErrorSeverity.ERROR,
    "数据完整性错误", "违反数据库约束",
    "请检查数据是否符合约束条件"
)

DB_TIMEOUT = define_error(
    "80005", ErrorCategory.DB, ErrorSeverity.ERROR,
    "数据库超时", "数据库操作超时",
    "请优化查询或增加超时时间"
)

DB_DEADLOCK = define_error(
    "80006", ErrorCategory.DB, ErrorSeverity.ERROR,
    "死锁", "检测到数据库死锁",
    "请重试操作"
)

# ============================================================
# 9xxxx - 未知错误
# ============================================================

UNK_ERROR = define_error(
    "90001", ErrorCategory.UNK, ErrorSeverity.ERROR,
    "未知错误", "发生未知错误",
    "请联系技术支持"
)

UNK_EXCEPTION = define_error(
    "90002", ErrorCategory.UNK, ErrorSeverity.ERROR,
    "未处理异常", "发生未处理的异常",
    "请查看错误日志获取详细信息"
)


# ============================================================
# 错误码工具函数
# ============================================================

# Python异常到错误码的映射
EXCEPTION_TO_ERROR_CODE = {
    # 认证相关
    'AuthenticationError': '10001',
    'PermissionError': '10004',
    'SessionExpired': '10005',

    # 业务相关
    'ValueError': '30002',
    'TypeError': '30002',
    'KeyError': '30001',
    'AttributeError': '50001',

    # 网络相关
    'ConnectionError': '70001',
    'TimeoutError': '70002',
    'SSLError': '70004',
    'ProxyError': '70005',
    'requests.exceptions.ConnectionError': '70001',
    'requests.exceptions.Timeout': '70002',
    'requests.exceptions.SSLError': '70004',
    'urllib3.exceptions.MaxRetryError': '70001',

    # 数据库相关
    'OperationalError': '80001',
    'IntegrityError': '80004',
    'DatabaseError': '80002',
    'sqlalchemy.exc.OperationalError': '80001',
    'sqlalchemy.exc.IntegrityError': '80004',
    'sqlite3.OperationalError': '80001',

    # 外部服务
    'openai.error.RateLimitError': '40003',
    'openai.error.APIError': '40201',
    'openai.error.Timeout': '40002',

    # 系统相关
    'MemoryError': '50004',
    'OSError': '50001',
    'IOError': '60002',
    'FileNotFoundError': '60002',

    # JSON相关
    'JSONDecodeError': '30003',
    'json.JSONDecodeError': '30003',
}

# 关键词到错误码的映射
KEYWORD_TO_ERROR_CODE = {
    # 认证
    'login fail': '10001',
    'password': '10001',
    'unauthorized': '10004',
    'forbidden': '10004',
    'token expired': '10002',
    'session expired': '10005',
    'cookie expired': '10102',
    'qr code expired': '10103',
    'account locked': '10006',
    'account disabled': '10007',

    # 平台
    'platform error': '40101',
    'platform unavailable': '40102',
    'zhihu': '40101',
    'weixin': '40101',
    'wechat': '40101',
    'publish fail': '20003',
    'captcha': '40301',
    '验证码': '40301',

    # API
    'api error': '40001',
    'rate limit': '40003',
    'quota': '40004',
    'openai': '40201',

    # 网络
    'connection': '70001',
    'timeout': '70002',
    'ssl': '70004',
    'dns': '70003',
    'proxy': '70005',

    # 数据库
    'database': '80002',
    'sql': '80002',
    'query': '80002',
    'transaction': '80003',
    'integrity': '80004',
    'deadlock': '80006',

    # 验证
    'invalid': '30002',
    'missing': '30001',
    'required': '30001',
    'json': '30003',

    # 资源
    'not found': '60001',
    'file not found': '60002',
    'already exists': '60003',

    # 系统
    'memory': '50004',
    'disk full': '50005',
    'out of memory': '50004',
    'config': '50002',
}


def classify_error(error_message: str, exception_type: str = None) -> Dict:
    """
    根据错误信息分类错误

    Args:
        error_message: 错误消息
        exception_type: 异常类型名称

    Returns:
        分类结果，包含 code, category, severity, name 等
    """
    error_code = None

    # 1. 先尝试根据异常类型匹配
    if exception_type:
        # 完整类型名匹配
        if exception_type in EXCEPTION_TO_ERROR_CODE:
            error_code = EXCEPTION_TO_ERROR_CODE[exception_type]
        else:
            # 简短类型名匹配
            short_type = exception_type.split('.')[-1]
            if short_type in EXCEPTION_TO_ERROR_CODE:
                error_code = EXCEPTION_TO_ERROR_CODE[short_type]

    # 2. 如果没匹配到，根据错误消息关键词匹配
    if not error_code and error_message:
        msg_lower = error_message.lower()
        for keyword, code in KEYWORD_TO_ERROR_CODE.items():
            if keyword in msg_lower:
                error_code = code
                break

    # 3. 默认为未知错误
    if not error_code:
        error_code = '90001'

    # 获取错误定义
    error_def = ERROR_DEFINITIONS.get(error_code)
    if error_def:
        return {
            'code': error_def.full_code,
            'category': error_def.category.name,
            'category_name': error_def.category.name_cn,
            'severity': error_def.severity.value,
            'name': error_def.name,
            'description': error_def.description,
            'solution': error_def.solution
        }

    # 未找到定义
    return {
        'code': f'ERR-{error_code}',
        'category': 'UNK',
        'category_name': '未知错误',
        'severity': 'ERROR',
        'name': '未知错误',
        'description': error_message[:100] if error_message else '未知错误',
        'solution': ''
    }


def get_error_by_code(error_code: str) -> Optional[ErrorDefinition]:
    """根据错误码获取错误定义"""
    # 移除ERR-前缀
    code = error_code.replace('ERR-', '')
    return ERROR_DEFINITIONS.get(code)


def get_errors_by_category(category: ErrorCategory) -> List[ErrorDefinition]:
    """获取某分类下的所有错误定义"""
    return [e for e in ERROR_DEFINITIONS.values() if e.category == category]


def get_errors_by_severity(severity: ErrorSeverity) -> List[ErrorDefinition]:
    """获取某严重级别的所有错误定义"""
    return [e for e in ERROR_DEFINITIONS.values() if e.severity == severity]


def get_all_categories() -> List[Dict]:
    """获取所有错误分类"""
    return [
        {
            'code': cat.code_prefix,
            'name': cat.name,
            'name_cn': cat.name_cn,
            'name_en': cat.name_en,
            'count': len(get_errors_by_category(cat))
        }
        for cat in ErrorCategory
    ]


# 导出
__all__ = [
    'ErrorSeverity',
    'ErrorCategory',
    'ErrorDefinition',
    'ERROR_DEFINITIONS',
    'classify_error',
    'get_error_by_code',
    'get_errors_by_category',
    'get_errors_by_severity',
    'get_all_categories',
    # 具体错误码常量...
]
