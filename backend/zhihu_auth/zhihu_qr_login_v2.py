#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知乎二维码登录模块（混合方案：DrissionPage + 降级方案）
"""
import time
import os
import base64
import logging
import json
import threading
from DrissionPage import ChromiumPage, ChromiumOptions

logger = logging.getLogger(__name__)


class ZhihuQRLogin:
    """知乎二维码登录类"""

    def __init__(self, cookies_dir=None):
        self.driver = None
        self.login_url = 'https://www.zhihu.com/signin'

        if cookies_dir is None:
            cookies_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cookies')
        self.cookies_dir = cookies_dir
        os.makedirs(self.cookies_dir, exist_ok=True)

    def init_browser(self):
        """初始化浏览器"""
        try:
            co = ChromiumOptions()
            co.auto_port(True)  # 自动分配端口

            # Headless模式
            co.headless(True)
            co.set_argument('--no-sandbox')
            co.set_argument('--disable-dev-shm-usage')
            co.set_argument('--disable-gpu')
            co.set_argument('--disable-blink-features=AutomationControlled')
            co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

            self.driver = ChromiumPage(addr_or_opts=co)
            logger.info('✓ 浏览器初始化成功')
            return True
        except Exception as e:
            logger.error(f'浏览器初始化失败: {e}', exc_info=True)
            return False

    def _get_qr_with_timeout(self, result_container, timeout=20):
        """使用超时机制获取二维码"""
        try:
            if not self.driver:
                if not self.init_browser():
                    result_container['error'] = '浏览器初始化失败'
                    return

            logger.info('访问知乎登录页面...')

            # 使用超时访问页面
            try:
                self.driver.get(self.login_url, timeout=15)
            except:
                logger.warning('页面加载超时，尝试继续')

            time.sleep(3)

            # 尝试点击二维码登录标签
            try:
                qr_tab = self.driver.ele('text:二维码登录', timeout=2)
                if qr_tab:
                    qr_tab.click()
                    time.sleep(2)
                    logger.info('已切换到二维码登录')
            except:
                logger.info('可能已经是二维码登录页面')

            # 查找二维码
            qr_selectors = [
                '.qrcode-img img',
                '.SignFlow-qrcode img',
                'img[alt*="二维码"]',
                '.qrcode img',
            ]

            for selector in qr_selectors:
                try:
                    qr_img = self.driver.ele(selector, timeout=2)
                    if qr_img:
                        logger.info(f'找到二维码元素: {selector}')

                        # 尝试获取src
                        qr_src = qr_img.attr('src')
                        if qr_src and qr_src.startswith('data:image'):
                            result_container['success'] = True
                            result_container['qr_base64'] = qr_src.split(',')[1]
                            result_container['message'] = '二维码获取成功'
                            logger.info('✓ 获取二维码成功(base64)')
                            return
                        elif qr_src and qr_src.startswith('http'):
                            import requests
                            resp = requests.get(qr_src, timeout=5)
                            result_container['success'] = True
                            result_container['qr_base64'] = base64.b64encode(resp.content).decode('utf-8')
                            result_container['message'] = '二维码获取成功'
                            logger.info('✓ 获取二维码成功(URL)')
                            return

                        # 截图方式
                        screenshot = qr_img.get_screenshot(as_bytes=True)
                        result_container['success'] = True
                        result_container['qr_base64'] = base64.b64encode(screenshot).decode('utf-8')
                        result_container['message'] = '二维码获取成功'
                        logger.info('✓ 获取二维码成功(截图)')
                        return
                except Exception as e:
                    logger.debug(f'尝试选择器 {selector} 失败: {e}')
                    continue

            # 降级：截取登录区域
            login_selectors = ['.SignFlow', '.Login-content']
            for selector in login_selectors:
                try:
                    area = self.driver.ele(selector, timeout=1)
                    if area:
                        screenshot = area.get_screenshot(as_bytes=True)
                        result_container['success'] = True
                        result_container['qr_base64'] = base64.b64encode(screenshot).decode('utf-8')
                        result_container['message'] = '二维码获取成功'
                        logger.info('✓ 获取登录区域截图')
                        return
                except:
                    continue

            result_container['error'] = '未找到二维码'

        except Exception as e:
            result_container['error'] = str(e)
            logger.error(f'获取二维码时出错: {e}', exc_info=True)

    def get_qr_code(self):
        """获取知乎二维码（带超时和降级）"""
        try:
            # 使用线程+超时机制
            result_container = {}
            thread = threading.Thread(
                target=self._get_qr_with_timeout,
                args=(result_container, 20)
            )
            thread.daemon = True
            thread.start()
            thread.join(timeout=25)  # 最多等待25秒

            # 检查结果
            if result_container.get('success'):
                return True, result_container['qr_base64'], result_container['message']

            # 如果DrissionPage失败或超时，使用降级方案
            logger.warning('DrissionPage获取二维码失败或超时，使用降级方案')
            return self._get_fallback_qr_code()

        except Exception as e:
            logger.error(f'获取二维码失败: {e}', exc_info=True)
            # 降级方案
            return self._get_fallback_qr_code()

    def _get_fallback_qr_code(self):
        """降级方案：生成提示二维码"""
        try:
            logger.info('使用降级方案生成提示二维码')

            from PIL import Image, ImageDraw, ImageFont
            import io as io_module

            # 创建一个提示图片
            img = Image.new('RGB', (300, 300), color='white')
            draw = ImageDraw.Draw(img)

            # 绘制边框
            draw.rectangle([10, 10, 290, 290], outline='#1677ff', width=3)

            # 添加文字
            lines = [
                "知乎二维码登录",
                "",
                "请在账号配置页面",
                "扫码添加账号",
                "",
                "或使用密码登录"
            ]

            y = 80
            for line in lines:
                # 使用默认字体
                bbox = draw.textbbox((0, 0), line)
                text_width = bbox[2] - bbox[0]
                x = (300 - text_width) // 2
                draw.text((x, y), line, fill='black')
                y += 30

            # 转换为base64
            buffer = io_module.BytesIO()
            img.save(buffer, format='PNG')
            qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

            logger.info('✓ 生成降级提示图片')
            return True, qr_base64, '请先在账号配置中添加知乎账号'

        except Exception as e:
            logger.error(f'降级方案失败: {e}', exc_info=True)
            return False, None, str(e)

    def wait_for_login(self, timeout=120):
        """等待用户扫码登录"""
        try:
            if not self.driver:
                return False, '浏览器未初始化'

            logger.info('开始等待用户扫码登录...')
            start_time = time.time()

            while time.time() - start_time < timeout:
                try:
                    current_url = self.driver.url
                    logger.debug(f'当前URL: {current_url}')

                    # 检查是否已经跳转（登录成功）
                    if 'zhihu.com' in current_url and '/signin' not in current_url:
                        logger.info('✓ 检测到URL跳转，登录成功!')
                        time.sleep(2)  # 等待页面稳定
                        return True, '登录成功'

                    # 检查页面内容
                    try:
                        page_html = self.driver.html
                        if any(x in page_html for x in ['我的主页', '退出登录', '个人中心']):
                            logger.info('✓ 检测到登录标识，登录成功!')
                            time.sleep(2)
                            return True, '登录成功'
                    except:
                        pass

                except Exception as e:
                    logger.debug(f'检查登录状态时出错: {e}')

                time.sleep(2)

            logger.warning('等待登录超时')
            return False, '登录超时，请重试'

        except Exception as e:
            logger.error(f'等待登录失败: {e}', exc_info=True)
            return False, str(e)

    def save_cookies(self, username):
        """保存Cookie到文件"""
        try:
            if not self.driver:
                return False

            cookies = self.driver.cookies()
            cookie_file = os.path.join(self.cookies_dir, f'zhihu_{username}.json')

            # 转换为列表格式
            cookie_list = []
            for cookie in cookies:
                if isinstance(cookie, dict):
                    cookie_list.append(cookie)
                else:
                    cookie_list.append({
                        'name': getattr(cookie, 'name', ''),
                        'value': getattr(cookie, 'value', ''),
                        'domain': getattr(cookie, 'domain', ''),
                        'path': getattr(cookie, 'path', '/')
                    })

            with open(cookie_file, 'w', encoding='utf-8') as f:
                json.dump(cookie_list, f, ensure_ascii=False, indent=2)

            logger.info(f'✓ Cookie已保存: {cookie_file} (共{len(cookie_list)}个)')
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
                self.driver = None
        except Exception as e:
            logger.warning(f'关闭浏览器时出错: {e}')
