#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知乎二维码登录模块
实现知乎扫码登录
"""
import time
import os
import base64
import logging
import json
from DrissionPage import ChromiumPage, ChromiumOptions

logger = logging.getLogger(__name__)


class ZhihuQRLogin:
    """知乎二维码登录类"""

    def __init__(self, cookies_dir=None):
        """
        初始化二维码登录

        Args:
            cookies_dir: Cookie存储目录
        """
        self.driver = None
        self.qr_image_path = None
        self.login_url = 'https://www.zhihu.com/signin'

        if cookies_dir is None:
            cookies_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cookies')
        self.cookies_dir = cookies_dir
        os.makedirs(self.cookies_dir, exist_ok=True)

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
            logger.info('二维码登录浏览器初始化成功')
            return True
        except Exception as e:
            logger.error(f'浏览器初始化失败: {e}', exc_info=True)
            return False

    def get_qr_code(self):
        """
        获取知乎扫码登录的二维码

        Returns:
            (success, qr_image_base64, message)
        """
        try:
            if not self.driver:
                if not self.init_browser():
                    return False, None, '浏览器初始化失败'

            # 访问登录页面
            logger.info('访问知乎登录页面...')
            self.driver.get(self.login_url)
            time.sleep(3)

            # 尝试点击二维码登录标签
            try:
                qr_tab_selectors = [
                    'text:二维码登录',
                    'text:扫码登录',
                    '.SignFlow-qrcodeTab',
                    '@@data-za-detail-view-id=2152',
                ]

                for selector in qr_tab_selectors:
                    try:
                        qr_tab = self.driver.ele(selector, timeout=2)
                        if qr_tab:
                            logger.info(f'找到二维码登录标签: {selector}')
                            qr_tab.click()
                            time.sleep(2)
                            break
                    except:
                        continue
            except Exception as e:
                logger.warning(f'点击二维码登录标签失败: {e}')

            # 查找二维码图片
            qr_img = None
            qr_selectors = [
                '.qrcode-img img',
                '.SignFlow-qrcode img',
                'img[alt*="二维码"]',
                'canvas.qrcode',  # 有些网站用canvas显示二维码
            ]

            for selector in qr_selectors:
                try:
                    qr_img = self.driver.ele(selector, timeout=3)
                    if qr_img:
                        logger.info(f'找到二维码元素: {selector}')
                        break
                except:
                    continue

            if not qr_img:
                logger.error('未找到二维码图片元素')
                return False, None, '未找到二维码'

            # 获取二维码图片
            try:
                # 尝试获取图片src
                qr_src = qr_img.attr('src')

                if qr_src:
                    if qr_src.startswith('data:image'):
                        # Base64格式
                        qr_base64 = qr_src.split(',')[1]
                        logger.info('✓ 成功获取二维码(base64)')
                        return True, qr_base64, '二维码获取成功'
                    elif qr_src.startswith('http'):
                        # URL格式,需要下载
                        import requests
                        response = requests.get(qr_src)
                        qr_base64 = base64.b64encode(response.content).decode('utf-8')
                        logger.info('✓ 成功获取二维码(URL下载)')
                        return True, qr_base64, '二维码获取成功'
                else:
                    # 截图方式
                    screenshot = qr_img.get_screenshot(as_bytes=True)
                    qr_base64 = base64.b64encode(screenshot).decode('utf-8')
                    logger.info('✓ 成功获取二维码(截图)')
                    return True, qr_base64, '二维码获取成功'

            except Exception as e:
                logger.error(f'获取二维码失败: {e}', exc_info=True)
                return False, None, f'获取二维码失败: {str(e)}'

        except Exception as e:
            logger.error(f'获取二维码过程失败: {e}', exc_info=True)
            return False, None, str(e)

    def wait_for_login(self, timeout=120):
        """
        等待用户扫码登录

        Args:
            timeout: 超时时间(秒)

        Returns:
            (success, message)
        """
        try:
            start_time = time.time()

            while time.time() - start_time < timeout:
                try:
                    # 检查是否登录成功
                    current_url = self.driver.url

                    # 如果跳转到首页,说明登录成功
                    if 'zhihu.com' in current_url and '/signin' not in current_url:
                        logger.info('✓ 检测到登录成功!')
                        return True, '登录成功'

                    # 检查页面内容
                    page_html = self.driver.html
                    if any(indicator in page_html for indicator in ['我的主页', '退出登录', '个人中心']):
                        logger.info('✓ 检测到登录标识,登录成功!')
                        return True, '登录成功'

                except Exception as e:
                    logger.debug(f'检查登录状态时出错: {e}')

                time.sleep(2)

            return False, '登录超时'

        except Exception as e:
            logger.error(f'等待登录失败: {e}', exc_info=True)
            return False, str(e)

    def save_cookies(self, username):
        """
        保存登录后的Cookie

        Args:
            username: 用户名(用于cookie文件命名)

        Returns:
            bool: 是否保存成功
        """
        try:
            cookies = self.driver.cookies()
            cookie_file = os.path.join(self.cookies_dir, f'zhihu_{username}.json')

            # 转换cookie格式
            cookie_list = []
            for cookie in cookies:
                cookie_list.append(cookie)

            with open(cookie_file, 'w', encoding='utf-8') as f:
                json.dump(cookie_list, f, ensure_ascii=False, indent=2)

            logger.info(f'✓ Cookie已保存到: {cookie_file}')
            return True

        except Exception as e:
            logger.error(f'保存Cookie失败: {e}', exc_info=True)
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
