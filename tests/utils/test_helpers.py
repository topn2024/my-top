#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试辅助工具
提供测试数据生成、配置管理、认证等辅助功能
"""
import json
import random
import string
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def get_test_config() -> Dict[str, Any]:
    """
    获取测试配置

    Returns:
        测试配置字典
    """
    config_file = project_root / "tests" / "config" / "test_config.json"

    default_config = {
        "base_url": "http://localhost:3001",
        "timeout": 30,
        "test_user": {
            "username": "test_user",
            "password": "test_password_123",
            "email": "test@example.com"
        },
        "database": {
            "url": "sqlite:///test_topn.db",
            "echo": False
        },
        "api_endpoints": {
            "login": "/api/login",
            "logout": "/api/logout",
            "register": "/api/register",
            "articles": "/api/articles",
            "workflows": "/api/workflows",
            "publish": "/api/publish"
        }
    }

    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                default_config.update(file_config)
        except Exception as e:
            print(f"⚠️ 无法加载测试配置文件: {e}")

    # 从环境变量覆盖配置
    if os.getenv('TEST_BASE_URL'):
        default_config['base_url'] = os.getenv('TEST_BASE_URL')
    if os.getenv('TEST_TIMEOUT'):
        default_config['timeout'] = int(os.getenv('TEST_TIMEOUT'))

    return default_config


def generate_test_user_data() -> Dict[str, str]:
    """
    生成测试用户数据

    Returns:
        测试用户数据字典
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

    return {
        "username": f"test_user_{timestamp}_{random_suffix}",
        "password": f"test_password_{random_suffix}",
        "email": f"test_user_{timestamp}_{random_suffix}@example.com",
        "confirm_password": f"test_password_{random_suffix}"
    }


def generate_test_article_data() -> Dict[str, Any]:
    """
    生成测试文章数据

    Returns:
        测试文章数据字典
    """
    categories = ["technology", "business", "education", "health", "entertainment"]
    titles = [
        "人工智能技术发展趋势",
        "数字化转型的机遇与挑战",
        "云计算在企业中的应用",
        "大数据分析的商业价值",
        "物联网技术的创新应用"
    ]

    contents = [
        """
        随着科技的快速发展，人工智能技术正在深刻改变我们的生活和工作方式。
        从智能制造到智慧城市，从医疗诊断到金融分析，AI应用无处不在。
        本文将探讨AI技术的最新发展趋势，分析其在各个领域的应用前景，
        以及面临的机遇和挑战。通过深入分析技术特点和应用案例，
        为读者提供全面的技术洞察和发展建议。
        """,
        """
        数字化转型已成为企业发展的重要战略方向。在这个信息时代，
        如何有效利用数字技术提升运营效率、创新商业模式，
        成为每个企业都需要思考的问题。本文分析了数字化转型的核心要素，
        探讨了实施过程中的常见挑战，并提出了切实可行的解决方案。
        通过案例分析和最佳实践分享，帮助企业更好地推进数字化转型。
        """,
        """
        云计算技术的成熟为企业IT基础设施建设带来了革命性变化。
        从IaaS到PaaS再到SaaS，云服务模式不断创新，
        为企业提供了灵活、高效、成本可控的IT解决方案。
        本文深入分析了云计算的技术架构、服务模式和安全机制，
        并结合实际应用案例，展示了云计算在不同业务场景下的价值。
        """
    ]

    return {
        "title": random.choice(titles),
        "content": random.choice(contents),
        "category": random.choice(categories),
        "tags": ["AI", "技术", "创新"],
        "author": "Test Author",
        "status": "draft",
        "created_at": datetime.now().isoformat()
    }


def generate_test_workflow_data() -> Dict[str, Any]:
    """
    生成测试工作流数据

    Returns:
        测试工作流数据字典
    """
    workflow_names = [
        "AI内容生成工作流",
        "文章分析处理流程",
        "智能发布管理",
        "多平台内容分发",
        "自动化内容优化"
    ]

    workflow_steps = [
        {"step": 1, "action": "analyze", "config": {"model": "zhipu", "temperature": 0.7}},
        {"step": 2, "action": "generate", "config": {"length": 500, "style": "professional"}},
        {"step": 3, "action": "review", "config": {"auto_approve": False}},
        {"step": 4, "action": "publish", "config": {"platforms": ["weibo", "wechat"]}}
    ]

    return {
        "name": random.choice(workflow_names),
        "description": f"自动化工作流 - 创建于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "steps": workflow_steps,
        "enabled": True,
        "created_at": datetime.now().isoformat()
    }


def authenticate_user(client) -> bool:
    """
    为API客户端进行用户认证

    Args:
        client: API客户端实例

    Returns:
        认证是否成功
    """
    config = get_test_config()
    test_user = config['test_user']

    try:
        # 尝试登录
        login_data = {
            'username': test_user['username'],
            'password': test_user['password']
        }

        response = client.post("/api/login", data=login_data)

        if response.status_code in [200, 302]:
            return True
        else:
            # 如果登录失败，尝试注册新用户
            register_data = generate_test_user_data()

            register_response = client.post("/api/register", data=register_data)
            if register_response.status_code in [200, 201]:
                # 注册成功后再登录
                login_data = {
                    'username': register_data['username'],
                    'password': register_data['password']
                }
                login_response = client.post("/api/login", data=login_data)
                return login_response.status_code in [200, 302]

        return False

    except Exception as e:
        print(f"⚠️ 用户认证失败: {e}")
        return False


def generate_test_credentials() -> Dict[str, str]:
    """
    生成测试凭证

    Returns:
        测试用户名和密码字典
    """
    config = get_test_config()
    return {
        "username": config['test_user']['username'],
        "password": config['test_user']['password']
    }


def get_webdriver_config() -> Dict[str, Any]:
    """
    获取WebDriver配置

    Returns:
        WebDriver配置字典
    """
    config = get_test_config()

    webdriver_config = {
        "base_url": config.get('base_url', 'http://localhost:3001'),
        "headless": True,  # 默认无头模式
        "implicit_wait": 10,
        "page_load_timeout": 30,
        "webdriver_path": None,  # 使用系统PATH中的WebDriver
        "download_dir": str(project_root / "tests" / "downloads"),
        "screenshot_dir": str(project_root / "tests" / "screenshots")
    }

    # 从环境变量覆盖配置
    if os.getenv('TEST_HEADLESS') is not None:
        webdriver_config['headless'] = os.getenv('TEST_HEADLESS').lower() == 'true'
    if os.getenv('TEST_WEBDRIVER_PATH'):
        webdriver_config['webdriver_path'] = os.getenv('TEST_WEBDRIVER_PATH')

    # 创建必要的目录
    Path(webdriver_config['download_dir']).mkdir(exist_ok=True)
    Path(webdriver_config['screenshot_dir']).mkdir(exist_ok=True)

    return webdriver_config


def cleanup_test_data(data_type: str = "all"):
    """
    清理测试数据

    Args:
        data_type: 数据类型 ("users", "articles", "workflows", "all")
    """
    try:
        from models import engine, SessionLocal
        from sqlalchemy import text

        with SessionLocal() as session:
            if data_type in ["users", "all"]:
                # 删除测试用户（以test_开头的用户名）
                session.execute(text("DELETE FROM users WHERE username LIKE 'test_%'"))

            if data_type in ["articles", "all"]:
                # 删除测试文章
                session.execute(text("DELETE FROM articles WHERE title LIKE 'test_%' OR content LIKE 'test_%'"))

            if data_type in ["workflows", "all"]:
                # 删除测试工作流
                session.execute(text("DELETE FROM workflows WHERE name LIKE 'test_%'"))

            session.commit()
            print(f"✓ 清理测试数据: {data_type}")

    except Exception as e:
        print(f"⚠️ 清理测试数据失败: {e}")


def save_test_result(test_name: str, result: Dict[str, Any]):
    """
    保存测试结果

    Args:
        test_name: 测试名称
        result: 测试结果
    """
    results_file = project_root / "tests" / "reports" / "test_results.json"
    results_file.parent.mkdir(exist_ok=True)

    try:
        # 读取现有结果
        if results_file.exists():
            with open(results_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
        else:
            results = {}

        # 添加新结果
        results[test_name] = {
            **result,
            "timestamp": datetime.now().isoformat()
        }

        # 保存结果
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

    except Exception as e:
        print(f"⚠️ 保存测试结果失败: {e}")


def assert_test_condition(condition: bool, message: str, test_name: str = ""):
    """
    断言测试条件

    Args:
        condition: 条件表达式
        message: 错误消息
        test_name: 测试名称
    """
    if not condition:
        error_msg = f"测试失败: {message}"
        if test_name:
            error_msg = f"[{test_name}] {error_msg}"
        raise AssertionError(error_msg)


def random_string(length: int = 10) -> str:
    """
    生成随机字符串

    Args:
        length: 字符串长度

    Returns:
        随机字符串
    """
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def wait_for_condition(check_func, timeout: int = 30, interval: int = 1) -> bool:
    """
    等待条件满足

    Args:
        check_func: 检查函数，返回bool
        timeout: 超时时间（秒）
        interval: 检查间隔（秒）

    Returns:
        条件是否满足
    """
    import time

    start_time = time.time()

    while time.time() - start_time < timeout:
        if check_func():
            return True
        time.sleep(interval)

    return False


class TestTimer:
    """测试计时器"""

    def __init__(self, name: str):
        self.name = name
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        print(f"⏱️ 开始测试: {self.name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = datetime.now()
        duration = self.end_time - self.start_time
        print(f"⏱️ 完成测试: {self.name} - 耗时: {duration.total_seconds():.2f}秒")

    def get_duration(self) -> float:
        """获取执行时长"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0