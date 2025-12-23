#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统综合测试脚本
测试TOP_N系统的所有基本功能模块
"""
import sys
import os
from pathlib import Path
from datetime import datetime
import traceback

# 设置UTF-8编码输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加backend目录到路径
BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))


class TestResult:
    """测试结果收集器"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def add_pass(self, name):
        self.passed += 1
        print(f"  [PASS] {name}")

    def add_fail(self, name, reason=""):
        self.failed += 1
        self.errors.append((name, reason))
        print(f"  [FAIL] {name}: {reason}")

    def summary(self):
        total = self.passed + self.failed
        return self.passed, total


# ============================================================
# 测试1: 核心模型导入
# ============================================================
def test_core_models(result: TestResult):
    """测试核心模型导入"""
    print("\n[1] 核心模型导入测试")
    print("-" * 50)

    models_to_test = [
        ('Base', 'models'),
        ('engine', 'models'),
        ('SessionLocal', 'models'),
        ('User', 'models'),
        ('Workflow', 'models'),
        ('Article', 'models'),
        ('PlatformAccount', 'models'),
        ('PublishHistory', 'models'),
        ('PublishTask', 'models'),
        ('AnalysisPrompt', 'models'),
        ('ArticlePrompt', 'models'),
        ('PlatformStylePrompt', 'models'),
        ('PromptCombinationLog', 'models'),
    ]

    for model_name, module_name in models_to_test:
        try:
            module = __import__(module_name, fromlist=[model_name])
            obj = getattr(module, model_name)
            if obj is not None:
                result.add_pass(f"{module_name}.{model_name}")
            else:
                result.add_fail(f"{module_name}.{model_name}", "is None")
        except Exception as e:
            result.add_fail(f"{module_name}.{model_name}", str(e))


# ============================================================
# 测试2: 提示词模板模型导入
# ============================================================
def test_prompt_template_models(result: TestResult):
    """测试提示词模板模型导入"""
    print("\n[2] 提示词模板模型导入测试")
    print("-" * 50)

    models_to_test = [
        'PromptTemplate',
        'PromptTemplateCategory',
        'PromptExampleLibrary',
        'PromptTemplateUsageLog',
        'PromptTemplateAuditLog',
    ]

    for model_name in models_to_test:
        try:
            module = __import__('models_prompt_template', fromlist=[model_name])
            obj = getattr(module, model_name)
            if obj is not None:
                result.add_pass(f"models_prompt_template.{model_name}")
            else:
                result.add_fail(f"models_prompt_template.{model_name}", "is None")
        except Exception as e:
            result.add_fail(f"models_prompt_template.{model_name}", str(e))


# ============================================================
# 测试3: 认证系统导入
# ============================================================
def test_auth_system(result: TestResult):
    """测试认证系统导入"""
    print("\n[3] 认证系统导入测试")
    print("-" * 50)

    auth_items = [
        'ROLE_GUEST',
        'ROLE_USER',
        'ROLE_ADMIN',
        'hash_password',
        'verify_password',
        'create_user',
        'authenticate_user',
        'get_current_user',
        'login_required',
        'admin_required',
        'create_session',
        'destroy_session',
        'PAGE_PERMISSIONS',
    ]

    for item in auth_items:
        try:
            module = __import__('auth', fromlist=[item])
            obj = getattr(module, item)
            if obj is not None:
                result.add_pass(f"auth.{item}")
            else:
                result.add_fail(f"auth.{item}", "is None")
        except Exception as e:
            result.add_fail(f"auth.{item}", str(e))


# ============================================================
# 测试4: 服务层导入
# ============================================================
def test_services(result: TestResult):
    """测试服务层导入"""
    print("\n[4] 服务层导入测试")
    print("-" * 50)

    services_to_test = [
        ('AIService', 'services.ai_service'),
        ('AnalysisPromptService', 'services.analysis_prompt_service'),
        ('ArticlePromptService', 'services.article_prompt_service'),
        ('PlatformStyleService', 'services.platform_style_service'),
        ('PromptCombinationService', 'services.prompt_combination_service'),
        ('PromptTemplateService', 'services.prompt_template_service'),
        ('WorkflowService', 'services.workflow_service'),
        ('PublishService', 'services.publish_service'),
        ('AccountService', 'services.account_service'),
        ('LogService', 'services.log_service'),
    ]

    for class_name, module_name in services_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name])
            obj = getattr(module, class_name)
            if obj is not None:
                result.add_pass(f"{module_name}.{class_name}")
            else:
                result.add_fail(f"{module_name}.{class_name}", "is None")
        except Exception as e:
            result.add_fail(f"{module_name}.{class_name}", str(e))


# ============================================================
# 测试5: 蓝图导入
# ============================================================
def test_blueprints(result: TestResult):
    """测试蓝图导入"""
    print("\n[5] 蓝图导入测试")
    print("-" * 50)

    blueprints_to_test = [
        ('api_bp', 'blueprints.api'),
        ('pages_bp', 'blueprints.pages'),
        ('task_bp', 'blueprints.task_api'),
        ('admin_bp', 'blueprints.admin_api'),
        ('auth_bp', 'blueprints.auth'),
        ('bp', 'blueprints.prompt_template_api'),
        ('analysis_prompt_bp', 'blueprints.analysis_prompt_api'),
        ('article_prompt_bp', 'blueprints.article_prompt_api'),
        ('platform_style_bp', 'blueprints.platform_style_api'),
        ('combination_bp', 'blueprints.prompt_combination_api'),
    ]

    for bp_name, module_name in blueprints_to_test:
        try:
            module = __import__(module_name, fromlist=[bp_name])
            obj = getattr(module, bp_name)
            if obj is not None:
                result.add_pass(f"{module_name}.{bp_name}")
            else:
                result.add_fail(f"{module_name}.{bp_name}", "is None")
        except Exception as e:
            result.add_fail(f"{module_name}.{bp_name}", str(e))


# ============================================================
# 测试6: 数据库连接
# ============================================================
def test_database_connection(result: TestResult):
    """测试数据库连接"""
    print("\n[6] 数据库连接测试")
    print("-" * 50)

    try:
        from models import engine
        from sqlalchemy import text

        with engine.connect() as conn:
            db_result = conn.execute(text("SELECT 1"))
            row = db_result.fetchone()
            if row and row[0] == 1:
                result.add_pass("database connection")
            else:
                result.add_fail("database connection", "query returned unexpected result")
    except Exception as e:
        result.add_fail("database connection", str(e))

    # 测试表存在
    try:
        from models import engine
        from sqlalchemy import inspect

        inspector = inspect(engine)
        tables = set(inspector.get_table_names())

        required_tables = ['users', 'workflows', 'articles', 'platform_accounts']
        for table in required_tables:
            if table in tables:
                result.add_pass(f"table: {table}")
            else:
                result.add_fail(f"table: {table}", "not found")
    except Exception as e:
        result.add_fail("table inspection", str(e))


# ============================================================
# 测试7: 配置系统
# ============================================================
def test_config(result: TestResult):
    """测试配置系统"""
    print("\n[7] 配置系统测试")
    print("-" * 50)

    try:
        from config import Config, get_config

        # 测试配置类
        if hasattr(Config, 'SECRET_KEY'):
            result.add_pass("Config.SECRET_KEY")
        else:
            result.add_fail("Config.SECRET_KEY", "not found")

        if hasattr(Config, 'UPLOAD_FOLDER'):
            result.add_pass("Config.UPLOAD_FOLDER")
        else:
            result.add_fail("Config.UPLOAD_FOLDER", "not found")

        if hasattr(Config, 'LOGS_FOLDER'):
            result.add_pass("Config.LOGS_FOLDER")
        else:
            result.add_fail("Config.LOGS_FOLDER", "not found")

        # 测试get_config函数
        config = get_config()
        if config is not None:
            result.add_pass("get_config()")
        else:
            result.add_fail("get_config()", "returned None")

    except Exception as e:
        result.add_fail("config import", str(e))


# ============================================================
# 测试8: 日志系统
# ============================================================
def test_logging_system(result: TestResult):
    """测试日志系统"""
    print("\n[8] 日志系统测试")
    print("-" * 50)

    try:
        from logger_config import setup_logger, log_service_call, log_api_request

        result.add_pass("logger_config.setup_logger")
        result.add_pass("logger_config.log_service_call")
        result.add_pass("logger_config.log_api_request")

        # 测试创建logger
        logger = setup_logger("test_module")
        if logger is not None:
            result.add_pass("setup_logger('test_module')")
        else:
            result.add_fail("setup_logger('test_module')", "returned None")

    except Exception as e:
        result.add_fail("logger_config import", str(e))


# ============================================================
# 测试9: 日志服务功能
# ============================================================
def test_log_service(result: TestResult):
    """测试日志服务功能"""
    print("\n[9] 日志服务功能测试")
    print("-" * 50)

    try:
        from services.log_service import LogService, get_log_service

        log_service = get_log_service()

        # 测试获取日志文件列表
        files = log_service.get_log_files()
        if isinstance(files, list):
            result.add_pass("LogService.get_log_files()")
        else:
            result.add_fail("LogService.get_log_files()", f"expected list, got {type(files)}")

        # 测试获取日志尾部
        tail_result = log_service.tail_logs('all.log', 10)
        if isinstance(tail_result, dict) and 'logs' in tail_result:
            result.add_pass("LogService.tail_logs()")
        else:
            result.add_fail("LogService.tail_logs()", "invalid return format")

        # 测试搜索日志
        search_result = log_service.search_logs(keyword='INFO', limit=5)
        if isinstance(search_result, dict) and 'logs' in search_result:
            result.add_pass("LogService.search_logs()")
        else:
            result.add_fail("LogService.search_logs()", "invalid return format")

        # 测试错误统计
        error_stats = log_service.get_error_stats(24)
        if isinstance(error_stats, dict):
            result.add_pass("LogService.get_error_stats()")
        else:
            result.add_fail("LogService.get_error_stats()", f"expected dict, got {type(error_stats)}")

        # 测试性能统计
        perf_stats = log_service.get_performance_stats(24)
        if isinstance(perf_stats, dict):
            result.add_pass("LogService.get_performance_stats()")
        else:
            result.add_fail("LogService.get_performance_stats()", f"expected dict, got {type(perf_stats)}")

    except Exception as e:
        result.add_fail("log_service test", str(e))


# ============================================================
# 测试10: Flask应用工厂
# ============================================================
def test_app_factory(result: TestResult):
    """测试Flask应用工厂"""
    print("\n[10] Flask应用工厂测试")
    print("-" * 50)

    try:
        from app_factory import create_app, app

        if app is not None:
            result.add_pass("app_factory.app")
        else:
            result.add_fail("app_factory.app", "is None")

        if callable(create_app):
            result.add_pass("app_factory.create_app")
        else:
            result.add_fail("app_factory.create_app", "not callable")

        # 测试应用配置
        if hasattr(app, 'config'):
            result.add_pass("app.config")
        else:
            result.add_fail("app.config", "not found")

        # 测试蓝图注册
        if len(app.blueprints) > 0:
            result.add_pass(f"blueprints registered ({len(app.blueprints)})")
        else:
            result.add_fail("blueprints registered", "no blueprints found")

    except Exception as e:
        result.add_fail("app_factory test", str(e))


# ============================================================
# 测试11: API路由注册
# ============================================================
def test_api_routes(result: TestResult):
    """测试API路由注册"""
    print("\n[11] API路由注册测试")
    print("-" * 50)

    try:
        from app_factory import app

        # 检查关键路由
        routes = [rule.rule for rule in app.url_map.iter_rules()]

        key_routes = [
            '/api/auth/login',
            '/api/auth/logout',
            '/api/generate_articles',
            '/api/accounts',
            '/api/workflow/list',
            '/api/admin/logs/files',
            '/api/admin/logs/tail',
            '/api/admin/logs/search',
            '/api/admin/logs/stats/errors',
            '/api/admin/logs/stats/performance',
        ]

        for route in key_routes:
            if route in routes:
                result.add_pass(f"route: {route}")
            else:
                result.add_fail(f"route: {route}", "not registered")

    except Exception as e:
        result.add_fail("api routes test", str(e))


# ============================================================
# 测试12: 密码加密功能
# ============================================================
def test_password_functions(result: TestResult):
    """测试密码加密功能"""
    print("\n[12] 密码加密功能测试")
    print("-" * 50)

    try:
        from auth import hash_password, verify_password

        test_password = "TestPassword123!"

        # 测试哈希
        hashed = hash_password(test_password)
        if hashed and len(hashed) > 0:
            result.add_pass("hash_password()")
        else:
            result.add_fail("hash_password()", "returned empty")

        # 测试验证正确密码
        if verify_password(hashed, test_password):
            result.add_pass("verify_password(correct)")
        else:
            result.add_fail("verify_password(correct)", "failed to verify")

        # 测试验证错误密码
        if not verify_password(hashed, "WrongPassword"):
            result.add_pass("verify_password(wrong)")
        else:
            result.add_fail("verify_password(wrong)", "should reject wrong password")

    except Exception as e:
        result.add_fail("password functions", str(e))


# ============================================================
# 主函数
# ============================================================
def main():
    """运行所有系统测试"""
    print("=" * 70)
    print("  TOP_N 系统综合测试")
    print(f"  执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    result = TestResult()

    # 运行所有测试
    test_functions = [
        test_core_models,
        test_prompt_template_models,
        test_auth_system,
        test_services,
        test_blueprints,
        test_database_connection,
        test_config,
        test_logging_system,
        test_log_service,
        test_app_factory,
        test_api_routes,
        test_password_functions,
    ]

    for test_func in test_functions:
        try:
            test_func(result)
        except Exception as e:
            print(f"\n  [ERROR] {test_func.__name__}: {e}")
            traceback.print_exc()
            result.failed += 1

    # 输出总结
    passed, total = result.summary()

    print("\n" + "=" * 70)
    print("  测试总结")
    print("=" * 70)
    print(f"\n  通过: {passed}/{total}")
    print(f"  失败: {result.failed}")
    print(f"  通过率: {passed/total*100:.1f}%")

    if result.errors:
        print("\n  失败详情:")
        for name, reason in result.errors:
            print(f"    - {name}: {reason}")

    print("\n" + "=" * 70)
    if result.failed == 0:
        print("  [SUCCESS] 所有测试通过！系统状态健康。")
    else:
        print("  [WARNING] 部分测试失败，请检查上述错误。")
    print("=" * 70)

    return 0 if result.failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
