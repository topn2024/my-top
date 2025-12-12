#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知乎Cookie登录模块
使用已保存的Cookie进行登录
"""
import os
import json
import logging
from DrissionPage import ChromiumPage, ChromiumOptions

logger = logging.getLogger(__name__)


class ZhihuCookieLogin:
    """知乎Cookie登录类"""

    def __init__(self, cookies_dir=None):
        """
        初始化Cookie登录

        Args:
            cookies_dir: Cookie存储目录
        """
        if cookies_dir is None:
            cookies_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cookies')
        self.cookies_dir = cookies_dir
        os.makedirs(self.cookies_dir, exist_ok=True)
        self.driver = None

    def init_browser(self):
        """初始化浏览器"""
        try:
            co = ChromiumOptions()

            # 服务器环境检测
            is_server = not os.environ.get('DISPLAY')
            if is_server:
                logger.info("检测到服务器环境，使用headless模式")
                co.headless(True)
                co.set_argument('--no-sandbox')
                co.set_argument('--disable-dev-shm-usage')
                co.set_argument('--disable-gpu')
            else:
                co.headless(False)

            co.set_argument('--disable-blink-features=AutomationControlled')
            co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

            self.driver = ChromiumPage(addr_or_opts=co)
            logger.info('Cookie登录浏览器初始化成功')
            return True
        except Exception as e:
            logger.error(f'浏览器初始化失败: {e}', exc_info=True)
            return False

    def load_cookies(self, username):
        """
        加载Cookie并登录

        Args:
            username: 用户名(用于查找cookie文件)

        Returns:
            (success, message)
        """
        try:
            cookie_file = os.path.join(self.cookies_dir, f'zhihu_{username}.json')

            if not os.path.exists(cookie_file):
                return False, f'Cookie文件不存在: {cookie_file}'

            # 初始化浏览器
            if not self.driver:
                if not self.init_browser():
                    return False, '浏览器初始化失败'

            # 加载Cookie
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)

            # 访问知乎首页
            self.driver.get('https://www.zhihu.com')

            # 设置Cookie
            for cookie in cookies:
                try:
                    self.driver.set.cookies(cookie)
                except Exception as e:
                    logger.warning(f'设置Cookie失败: {e}')

            # 刷新页面验证登录
            self.driver.refresh()

            # 验证是否登录成功
            if self.verify_login():
                logger.info(f'✓ Cookie登录成功: {username}')
                return True, '登录成功'
            else:
                return False, 'Cookie已过期，请重新登录'

        except Exception as e:
            logger.error(f'Cookie登录失败: {e}', exc_info=True)
            return False, str(e)

    def verify_login(self):
        """验证是否已登录"""
        try:
            import time
            time.sleep(2)

            page_html = self.driver.html
            # 检查登录标识
            if any(indicator in page_html for indicator in ['我的主页', '退出登录', '个人中心']):
                return True

            # 检查是否有登录按钮（未登录状态）
            if '登录' in page_html or 'signin' in page_html:
                return False

            return True
        except Exception as e:
            logger.error(f'验证登录状态失败: {e}')
            return False

    def get_driver(self):
        """获取浏览器驱动"""
        return self.driver

    def close(self):
        """关闭浏览器"""
        try:
            if self.driver:
                self.driver.quit()
                logger.info('浏览器已关闭')
        except Exception as e:
            logger.warning(f'关闭浏览器时出错: {e}')
