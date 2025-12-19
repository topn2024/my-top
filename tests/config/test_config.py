#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试配置管理
提供不同环境的测试配置
"""
import os
import json
from typing import Dict, Any, Optional
from pathlib import Path


class TestConfig:
    """测试配置类"""

    def __init__(self, environment: str = None):
        """
        初始化测试配置

        Args:
            environment: 环境名称 (development, staging, production)
        """
        self.environment = environment or os.getenv('TEST_ENVIRONMENT', 'development')
        self.config_dir = Path(__file__).parent
        self.project_root = self.config_dir.parent.parent
        self._config = None

    @property
    def config(self) -> Dict[str, Any]:
        """获取配置字典"""
        if self._config is None:
            self._config = self._load_config()
        return self._config

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        # 基础配置
        base_config = self._load_json_file('base_config.json')

        # 环境特定配置
        env_config = self._load_json_file(f'{self.environment}_config.json')

        # 本地覆盖配置
        local_config = self._load_json_file('local_config.json')

        # 合并配置
        config = {}
        config.update(base_config)
        config.update(env_config)
        config.update(local_config)

        # 环境变量覆盖
        config.update(self._get_env_overrides())

        # 添加动态路径
        config['paths'] = self._get_paths(config)

        return config

    def _load_json_file(self, filename: str) -> Dict[str, Any]:
        """加载JSON配置文件"""
        file_path = self.config_dir / filename

        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ 无法加载配置文件 {filename}: {e}")

        return {}

    def _get_env_overrides(self) -> Dict[str, Any]:
        """获取环境变量覆盖"""
        env_mappings = {
            'TEST_BASE_URL': ('web', 'base_url'),
            'TEST_API_URL': ('api', 'base_url'),
            'TEST_DATABASE_URL': ('database', 'url'),
            'TEST_TIMEOUT': ('api', 'timeout'),
            'TEST_HEADLESS': ('ui', 'headless'),
            'TEST_IMPLICIT_WAIT': ('ui', 'implicit_wait'),
            'TEST_PAGE_LOAD_TIMEOUT': ('ui', 'page_load_timeout'),
            'TEST_PARALLEL': ('test', 'parallel'),
            'TEST_COVERAGE': ('test', 'coverage'),
            'TEST_RETRY': ('test', 'retry'),
        }

        env_config = {}
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # 处理嵌套配置路径
                self._set_nested_value(env_config, config_path, self._convert_env_value(value))

        return env_config

    def _set_nested_value(self, config_dict: Dict, path: tuple, value: Any):
        """设置嵌套配置值"""
        current = config_dict
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value

    def _convert_env_value(self, value: str) -> Any:
        """转换环境变量值类型"""
        # 布尔值
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'

        # 整数
        try:
            return int(value)
        except ValueError:
            pass

        # 浮点数
        try:
            return float(value)
        except ValueError:
            pass

        # 字符串
        return value

    def _get_paths(self, config: Dict[str, Any]) -> Dict[str, str]:
        """获取动态路径配置"""
        base_paths = {
            'project_root': str(self.project_root),
            'tests_dir': str(self.project_root / 'tests'),
            'reports_dir': str(self.project_root / 'tests' / 'reports'),
            'screenshots_dir': str(self.project_root / 'tests' / 'screenshots'),
            'downloads_dir': str(self.project_root / 'tests' / 'downloads'),
            'fixtures_dir': str(self.project_root / 'tests' / 'fixtures'),
            'logs_dir': str(self.project_root / 'tests' / 'logs'),
        }

        # 合并配置中的路径
        if 'paths' in config:
            base_paths.update(config['paths'])

        return base_paths

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键（支持点号分隔的嵌套键）
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any):
        """
        设置配置值

        Args:
            key: 配置键
            value: 配置值
        """
        keys = key.split('.')
        current = self.config

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value

    def reload(self):
        """重新加载配置"""
        self._config = None

    def save_local_config(self, config_dict: Dict[str, Any]):
        """
        保存本地配置

        Args:
            config_dict: 要保存的配置字典
        """
        local_config_file = self.config_dir / 'local_config.json'

        try:
            with open(local_config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, ensure_ascii=False, indent=2)
            print(f"✓ 本地配置已保存: {local_config_file}")
        except Exception as e:
            print(f"⚠️ 保存本地配置失败: {e}")

    def create_test_user(self) -> Dict[str, str]:
        """
        创建测试用户配置

        Returns:
            测试用户配置
        """
        return {
            'username': os.getenv('TEST_USERNAME', 'test_user'),
            'password': os.getenv('TEST_PASSWORD', 'test_password_123'),
            'email': os.getenv('TEST_EMAIL', 'test@example.com')
        }

    def create_database_config(self) -> Dict[str, Any]:
        """
        创建数据库配置

        Returns:
            数据库配置
        """
        return {
            'url': os.getenv('TEST_DATABASE_URL', 'sqlite:///test_topn.db'),
            'echo': os.getenv('TEST_DATABASE_ECHO', 'false').lower() == 'true',
            'pool_size': int(os.getenv('TEST_DATABASE_POOL_SIZE', '5')),
            'max_overflow': int(os.getenv('TEST_DATABASE_MAX_OVERFLOW', '10'))
        }


# 全局配置实例
test_config = TestConfig()


def get_config(environment: str = None) -> TestConfig:
    """
    获取测试配置实例

    Args:
        environment: 环境名称

    Returns:
        测试配置实例
    """
    if environment:
        return TestConfig(environment)
    return test_config


def load_environment_config(env_name: str) -> Dict[str, Any]:
    """
    加载指定环境的配置

    Args:
        env_name: 环境名称

    Returns:
        环境配置字典
    """
    config_file = Path(__file__).parent / f'{env_name}_config.json'

    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return {}


def create_environment_config_file(env_name: str, config_dict: Dict[str, Any]):
    """
    创建环境配置文件

    Args:
        env_name: 环境名称
        config_dict: 配置字典
    """
    config_file = Path(__file__).parent / f'{env_name}_config.json'

    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, ensure_ascii=False, indent=2)
        print(f"✓ 环境配置文件已创建: {config_file}")
    except Exception as e:
        print(f"⚠️ 创建环境配置文件失败: {e}")


if __name__ == "__main__":
    # 示例用法
    config = get_config()

    print(f"当前环境: {config.environment}")
    print(f"Web基础URL: {config.get('web.base_url')}")
    print(f"API基础URL: {config.get('api.base_url')}")
    print(f"数据库URL: {config.get('database.url')}")

    # 创建本地配置示例
    local_config = {
        "web": {
            "base_url": "http://localhost:3001"
        },
        "test": {
            "parallel": True,
            "coverage": True,
            "retry": 2
        }
    }

    config.save_local_config(local_config)