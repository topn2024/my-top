#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知乎二维码登录模块（修复版：处理页面加载超时）
"""
import time
import os
import base64
import logging
import json
import signal
from contextlib import contextmanager
from DrissionPage import ChromiumPage, ChromiumOptions

logger = logging.getLogger(__name__)


class TimeoutException(Exception):
    pass


@contextmanager
def time_limit(seconds):
    """超时上下文管理器"""
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")

    # 只在Unix系统上使用signal
    if hasattr(signal, 'SIGALRM'):
        signal.signal(signal.SIGALRM, signal_handler)
        signal.alarm(seconds)
        try:
            yield
        finally:
            signal.alarm(0)
    else:
        # Windows系统，直接yield
        yield


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

            # 设置页面加载策略 - 不等待所有资源加载完成
            co.set_argument('--page-load-strategy=none')

            self.driver = ChromiumPage(addr_or_opts=co)

            # 设置更短的超时时间
            self.driver.set.timeouts(base=5, page_load=10, script=10)

            logger.info('✓ 浏览器初始化成功')
            return True
        except Exception as e:
            logger.error(f'浏览器初始化失败: {e}', exc_info=True)
            return False

    def get_qr_code(self):
        """获取知乎二维码"""
        try:
            if not self.driver:
                if not self.init_browser():
                    return self._generate_fallback_qr()

            logger.info('访问知乎登录页面...')

            # 强制访问页面，忽略超时
            try:
                self.driver.get(self.login_url)
            except Exception as e:
                logger.warning(f'页面加载异常（忽略）: {e}')

            # 等待DOM部分加载
            time.sleep(5)

            # 尝试停止页面加载
            try:
                self.driver.stop_loading()
                logger.info('已停止页面加载')
            except:
                pass

            time.sleep(2)

            # 尝试点击二维码登录标签
            logger.info('尝试切换到二维码登录...')
            qr_tab_selectors = [
                'text:二维码登录',
                'text:扫码登录',
                '.SignFlow-qrcodeTab',
            ]

            for selector in qr_tab_selectors:
                try:
                    qr_tab = self.driver.ele(selector, timeout=2)
                    if qr_tab:
                        logger.info(f'找到二维码标签: {selector}')
                        qr_tab.click()
                        time.sleep(3)
                        logger.info('已点击二维码标签')
                        break
                except Exception as e:
                    logger.debug(f'尝试选择器 {selector} 失败: {e}')
                    continue

            # 查找二维码图片元素
            logger.info('查找二维码元素...')
            qr_selectors = [
                'tag:img@@class:qrcode',  # DrissionPage特殊语法
                '.qrcode-img img',
                '.SignFlow-qrcode img',
                'img[alt*="二维码"]',
                '.qrcode img',
                'img[src*="qrcode"]',
                'img[src*="data:image"]',
            ]

            for selector in qr_selectors:
                try:
                    qr_img = self.driver.ele(selector, timeout=2)
                    if qr_img:
                        logger.info(f'✓ 找到二维码元素: {selector}')

                        # 方法1：尝试获取src属性
                        try:
                            qr_src = qr_img.attr('src')
                            if qr_src:
                                logger.info(f'二维码src类型: {qr_src[:50]}...')

                                if qr_src.startswith('data:image'):
                                    qr_base64 = qr_src.split(',')[1]
                                    logger.info('✓ 获取二维码成功(base64 from src)')
                                    return True, qr_base64, '二维码获取成功'

                                elif qr_src.startswith('http'):
                                    import requests
                                    resp = requests.get(qr_src, timeout=10)
                                    qr_base64 = base64.b64encode(resp.content).decode('utf-8')
                                    logger.info('✓ 获取二维码成功(URL download)')
                                    return True, qr_base64, '二维码获取成功'
                        except Exception as e:
                            logger.debug(f'获取src失败: {e}')

                        # 方法2：截图元素
                        try:
                            screenshot = qr_img.get_screenshot(as_bytes=True)
                            if screenshot and len(screenshot) > 100:
                                qr_base64 = base64.b64encode(screenshot).decode('utf-8')
                                logger.info(f'✓ 获取二维码成功(screenshot, {len(screenshot)} bytes)')
                                return True, qr_base64, '二维码获取成功'
                        except Exception as e:
                            logger.debug(f'截图失败: {e}')

                except Exception as e:
                    logger.debug(f'尝试选择器 {selector} 失败: {e}')
                    continue

            # 如果没找到二维码元素，尝试截取登录区域
            logger.warning('未找到二维码元素，尝试截取登录区域...')
            login_area_selectors = [
                '.SignFlow',
                '.Login-content',
                '[class*="SignFlow"]',
                'tag:div@@class=SignFlow',
            ]

            for selector in login_area_selectors:
                try:
                    area = self.driver.ele(selector, timeout=1)
                    if area:
                        logger.info(f'找到登录区域: {selector}')
                        screenshot = area.get_screenshot(as_bytes=True)
                        if screenshot and len(screenshot) > 100:
                            qr_base64 = base64.b64encode(screenshot).decode('utf-8')
                            logger.info(f'✓ 获取登录区域截图 ({len(screenshot)} bytes)')
                            return True, qr_base64, '二维码获取成功'
                except Exception as e:
                    logger.debug(f'尝试截取区域 {selector} 失败: {e}')
                    continue

            # 最后降级：生成提示图片
            logger.warning('所有方法失败，使用降级方案')
            return self._generate_fallback_qr()

        except Exception as e:
            logger.error(f'获取二维码失败: {e}', exc_info=True)
            return self._generate_fallback_qr()

    def _generate_fallback_qr(self):
        """生成降级提示图片"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import io as io_module

            img = Image.new('RGB', (300, 300), color='white')
            draw = ImageDraw.Draw(img)

            # 绘制边框
            draw.rectangle([10, 10, 290, 290], outline='#1677ff', width=3)

            # 添加文字提示
            lines = [
                "知乎二维码",
                "",
                "请在账号配置页面",
                "使用测试按钮",
                "进行扫码登录",
            ]

            y = 90
            for line in lines:
                bbox = draw.textbbox((0, 0), line)
                text_width = bbox[2] - bbox[0]
                x = (300 - text_width) // 2
                draw.text((x, y), line, fill='black')
                y += 35

            # 转换为base64
            buffer = io_module.BytesIO()
            img.save(buffer, format='PNG')
            qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

            logger.info('✓ 生成降级提示图片')
            return True, qr_base64, '请在账号配置中扫码登录'

        except Exception as e:
            logger.error(f'生成降级图片失败: {e}', exc_info=True)
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
                        time.sleep(2)
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
