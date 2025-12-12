#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
平台发布器抽象基类

定义所有平台发布器必须实现的接口
提供通用的Cookie管理、日志记录等功能
"""
from abc import ABC, abstractmethod
import json
import os
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class BasePlatformPublisher(ABC):
    """
    平台发布器抽象基类

    所有平台发布器必须继承此类并实现抽象方法
    """

    def __init__(self, platform_name: str):
        """
        初始化发布器

        Args:
            platform_name: 平台名称(zhihu, csdn, juejin等)
        """
        self.platform_name = platform_name

        # Cookie和日志目录
        self.cookies_dir = os.path.join(os.path.dirname(__file__), '..', 'cookies')
        self.logs_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
        os.makedirs(self.cookies_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)

        # 配置日志
        self.logger = self._setup_logger()

        # 浏览器实例(由子类初始化)
        self.driver = None

        self.logger.info(f'{platform_name} 发布器已初始化')

    def _setup_logger(self) -> logging.Logger:
        """配置日志记录器"""
        logger = logging.getLogger(f'{self.platform_name}_publisher')
        logger.setLevel(logging.INFO)

        # 避免重复添加handler
        if logger.handlers:
            return logger

        # 文件处理器
        log_file = os.path.join(self.logs_dir, f'{self.platform_name}_publish.log')
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)

        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    # ==================== Cookie管理 ====================

    def save_cookies(self, cookies: List[Dict], username: str) -> str:
        """
        保存Cookie到文件

        Args:
            cookies: Cookie列表
            username: 用户名(用于Cookie文件命名)

        Returns:
            Cookie文件路径
        """
        cookie_file = os.path.join(
            self.cookies_dir,
            f'{self.platform_name}_{username}.json'
        )

        with open(cookie_file, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)

        self.logger.info(f'Cookie已保存到: {cookie_file}')
        return cookie_file

    def load_cookies(self, username: str) -> Optional[List[Dict]]:
        """
        从文件加载Cookie

        Args:
            username: 用户名

        Returns:
            Cookie列表,如果文件不存在则返回None
        """
        cookie_file = os.path.join(
            self.cookies_dir,
            f'{self.platform_name}_{username}.json'
        )

        if not os.path.exists(cookie_file):
            self.logger.warning(f'Cookie文件不存在: {cookie_file}')
            return None

        try:
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)

            self.logger.info(f'Cookie已加载: {cookie_file}')
            return cookies
        except Exception as e:
            self.logger.error(f'加载Cookie失败: {e}')
            return None

    def delete_cookies(self, username: str) -> bool:
        """
        删除Cookie文件

        Args:
            username: 用户名

        Returns:
            是否删除成功
        """
        cookie_file = os.path.join(
            self.cookies_dir,
            f'{self.platform_name}_{username}.json'
        )

        if os.path.exists(cookie_file):
            try:
                os.remove(cookie_file)
                self.logger.info(f'Cookie已删除: {cookie_file}')
                return True
            except Exception as e:
                self.logger.error(f'删除Cookie失败: {e}')
                return False
        return False

    def cookies_exist(self, username: str) -> bool:
        """
        检查Cookie文件是否存在

        Args:
            username: 用户名

        Returns:
            Cookie文件是否存在
        """
        cookie_file = os.path.join(
            self.cookies_dir,
            f'{self.platform_name}_{username}.json'
        )
        return os.path.exists(cookie_file)

    # ==================== 抽象方法(子类必须实现) ====================

    @abstractmethod
    def login(self, username: str, password: str) -> Tuple[bool, str]:
        """
        账号密码登录

        Args:
            username: 用户名/手机号/邮箱
            password: 密码

        Returns:
            (是否成功, 消息)
        """
        pass

    @abstractmethod
    def login_with_qrcode(self) -> Tuple[bool, str, Optional[str]]:
        """
        二维码登录

        Returns:
            (是否成功, 消息, QR码图片路径/Base64)
        """
        pass

    @abstractmethod
    def is_logged_in(self) -> bool:
        """
        检查是否已登录

        Returns:
            是否已登录
        """
        pass

    @abstractmethod
    def publish_article(
        self,
        title: str,
        content: str,
        **kwargs
    ) -> Tuple[bool, str, Optional[str]]:
        """
        发布文章

        Args:
            title: 文章标题
            content: 文章内容
            **kwargs: 平台特定的其他参数

        Returns:
            (是否成功, 消息, 文章URL)
        """
        pass

    @abstractmethod
    def get_article_url_after_publish(self) -> Optional[str]:
        """
        获取发布后的文章URL

        Returns:
            文章URL,如果获取失败返回None
        """
        pass

    # ==================== 可选方法(子类可覆盖) ====================

    def refresh_cookies(self) -> bool:
        """
        刷新Cookie(子类可覆盖以实现特定逻辑)

        Returns:
            是否刷新成功
        """
        self.logger.info('刷新Cookie...')
        return True

    def close(self):
        """
        关闭浏览器和清理资源
        """
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info('浏览器已关闭')
            except Exception as e:
                self.logger.error(f'关闭浏览器失败: {e}')

    def __enter__(self):
        """支持with语句"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出时自动清理"""
        self.close()

    def __repr__(self):
        """字符串表示"""
        return f"<{self.__class__.__name__}(platform='{self.platform_name}')>"


# 自定义异常类
class PublisherException(Exception):
    """发布器基础异常"""
    pass


class LoginFailedException(PublisherException):
    """登录失败异常"""
    pass


class PublishFailedException(PublisherException):
    """发布失败异常"""
    pass


class CookieExpiredException(PublisherException):
    """Cookie过期异常"""
    pass


class NetworkException(PublisherException):
    """网络异常"""
    pass
