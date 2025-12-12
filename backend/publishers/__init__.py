#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多平台发布器模块

提供统一的工厂类接口用于创建不同平台的发布器实例
"""
from .base_publisher import (
    BasePlatformPublisher,
    PublisherException,
    LoginFailedException,
    PublishFailedException,
    CookieExpiredException,
    NetworkException
)
from .config import (
    PLATFORM_CONFIG,
    get_platform_config,
    get_supported_platforms,
    platform_supports_feature
)

# 延迟导入具体平台发布器(避免循环导入)
_publishers_cache = {}


def _get_publisher_class(platform_name: str):
    """
    获取平台发布器类(延迟导入)

    Args:
        platform_name: 平台名称

    Returns:
        发布器类

    Raises:
        ValueError: 不支持的平台
    """
    platform_name = platform_name.lower()

    # 检查缓存
    if platform_name in _publishers_cache:
        return _publishers_cache[platform_name]

    # 动态导入
    if platform_name == 'zhihu':
        try:
            from .zhihu_publisher import ZhihuPublisher
            _publishers_cache[platform_name] = ZhihuPublisher
            return ZhihuPublisher
        except ImportError as e:
            raise ImportError(f'知乎发布器导入失败: {e}')

    elif platform_name == 'csdn':
        try:
            from .csdn_publisher import CSDNPublisher
            _publishers_cache[platform_name] = CSDNPublisher
            return CSDNPublisher
        except ImportError as e:
            raise ImportError(f'CSDN发布器导入失败: {e}')

    elif platform_name == 'juejin':
        try:
            from .juejin_publisher import JuejinPublisher
            _publishers_cache[platform_name] = JuejinPublisher
            return JuejinPublisher
        except ImportError as e:
            raise ImportError(f'掘金发布器导入失败: {e}')

    else:
        raise ValueError(f'不支持的平台: {platform_name}')


class PlatformPublisherFactory:
    """
    平台发布器工厂类

    使用工厂模式创建不同平台的发布器实例
    """

    @staticmethod
    def create_publisher(platform_name: str) -> BasePlatformPublisher:
        """
        创建平台发布器实例

        Args:
            platform_name: 平台名称(zhihu, csdn, juejin等)

        Returns:
            对应平台的发布器实例

        Raises:
            ValueError: 不支持的平台
            ImportError: 发布器导入失败

        Example:
            >>> publisher = PlatformPublisherFactory.create_publisher('zhihu')
            >>> success, msg = publisher.login('username', 'password')
        """
        publisher_class = _get_publisher_class(platform_name)
        return publisher_class()

    @staticmethod
    def get_supported_platforms() -> list:
        """
        获取支持的平台列表

        Returns:
            平台名称列表

        Example:
            >>> platforms = PlatformPublisherFactory.get_supported_platforms()
            >>> print(platforms)
            ['zhihu', 'csdn', 'juejin']
        """
        return get_supported_platforms()

    @staticmethod
    def platform_exists(platform_name: str) -> bool:
        """
        检查平台是否存在

        Args:
            platform_name: 平台名称

        Returns:
            是否存在

        Example:
            >>> exists = PlatformPublisherFactory.platform_exists('zhihu')
            >>> print(exists)  # True
        """
        try:
            get_platform_config(platform_name)
            return True
        except ValueError:
            return False

    @staticmethod
    def get_platform_info(platform_name: str) -> dict:
        """
        获取平台信息

        Args:
            platform_name: 平台名称

        Returns:
            平台配置字典

        Raises:
            ValueError: 不支持的平台

        Example:
            >>> info = PlatformPublisherFactory.get_platform_info('csdn')
            >>> print(info['name'])  # CSDN
        """
        return get_platform_config(platform_name)


# 导出公共API
__all__ = [
    # 基类和异常
    'BasePlatformPublisher',
    'PublisherException',
    'LoginFailedException',
    'PublishFailedException',
    'CookieExpiredException',
    'NetworkException',

    # 工厂类
    'PlatformPublisherFactory',

    # 配置函数
    'get_platform_config',
    'get_supported_platforms',
    'platform_supports_feature',
    'PLATFORM_CONFIG'
]

# 版本信息
__version__ = '1.0.0'
__author__ = 'TOP_N Development Team'
