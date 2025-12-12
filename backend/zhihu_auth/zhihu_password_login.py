#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知乎密码登录模块
使用账号密码进行登录
"""
import os
import time
import logging
from DrissionPage import ChromiumPage, ChromiumOptions

logger = logging.getLogger(__name__)


class ZhihuPasswordLogin:
    """知乎密码登录类"""

    def __init__(self):
        self.driver = None
        self.login_url = 'https://www.zhihu.com/signin'

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
            logger.info('密码登录浏览器初始化成功')
            return True
        except Exception as e:
            logger.error(f'浏览器初始化失败: {e}', exc_info=True)
            return False

    def login(self, username, password):
        """
        使用账号密码登录

        Args:
            username: 用户名/手机号/邮箱
            password: 密码

        Returns:
            (success, message)
        """
        try:
            if not self.driver:
                if not self.init_browser():
                    return False, '浏览器初始化失败'

            # 访问登录页面
            logger.info('访问知乎登录页面...')
            self.driver.get(self.login_url)
            time.sleep(3)

            # 切换到密码登录
            try:
                password_tab_selectors = [
                    'text:密码登录',
                    'text:账号密码登录',
                    '.SignFlow-accountTab',
                ]

                for selector in password_tab_selectors:
                    try:
                        tab = self.driver.ele(selector, timeout=2)
                        if tab:
                            logger.info(f'找到密码登录标签: {selector}')
                            tab.click()
                            time.sleep(2)
                            break
                    except:
                        continue
            except Exception as e:
                logger.warning(f'切换密码登录标签失败: {e}')

            # 输入用户名
            username_input_selectors = [
                'input[name="username"]',
                'input[placeholder*="手机号"]',
                'input[placeholder*="邮箱"]',
                '.SignFlow-account input',
            ]

            username_input = None
            for selector in username_input_selectors:
                try:
                    username_input = self.driver.ele(selector, timeout=2)
                    if username_input:
                        logger.info(f'找到用户名输入框: {selector}')
                        break
                except:
                    continue

            if not username_input:
                return False, '未找到用户名输入框'

            username_input.input(username)
            time.sleep(1)

            # 输入密码
            password_input_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                '.SignFlow-password input',
            ]

            password_input = None
            for selector in password_input_selectors:
                try:
                    password_input = self.driver.ele(selector, timeout=2)
                    if password_input:
                        logger.info(f'找到密码输入框: {selector}')
                        break
                except:
                    continue

            if not password_input:
                return False, '未找到密码输入框'

            password_input.input(password)
            time.sleep(1)

            # 点击登录按钮
            login_btn_selectors = [
                'button:text("登录")',
                'button[type="submit"]',
                '.SignFlow-submitButton',
            ]

            login_btn = None
            for selector in login_btn_selectors:
                try:
                    login_btn = self.driver.ele(selector, timeout=2)
                    if login_btn:
                        logger.info(f'找到登录按钮: {selector}')
                        break
                except:
                    continue

            if not login_btn:
                return False, '未找到登录按钮'

            login_btn.click()
            logger.info('点击登录按钮...')

            # 等待登录完成
            time.sleep(5)

            # 验证登录
            if self.verify_login():
                logger.info('✓ 密码登录成功')
                return True, '登录成功'
            else:
                return False, '登录失败，请检查账号密码是否正确'

        except Exception as e:
            logger.error(f'密码登录失败: {e}', exc_info=True)
            return False, str(e)

    def verify_login(self):
        """验证是否已登录"""
        try:
            current_url = self.driver.url

            # 如果跳转离开登录页，说明登录成功
            if 'zhihu.com' in current_url and '/signin' not in current_url:
                return True

            # 检查页面内容
            page_html = self.driver.html
            if any(indicator in page_html for indicator in ['我的主页', '退出登录', '个人中心']):
                return True

            return False
        except Exception as e:
            logger.error(f'验证登录状态失败: {e}')
            return False

    def get_driver(self):
        """获取浏览器驱动"""
        return self.driver

    def get_cookies(self):
        """获取当前Cookie"""
        try:
            if self.driver:
                return list(self.driver.cookies())
            return []
        except Exception as e:
            logger.error(f'获取Cookie失败: {e}')
            return []

    def close(self):
        """关闭浏览器"""
        try:
            if self.driver:
                self.driver.quit()
                logger.info('浏览器已关闭')
        except Exception as e:
            logger.warning(f'关闭浏览器时出错: {e}')
