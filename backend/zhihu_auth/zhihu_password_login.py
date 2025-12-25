#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知乎密码登录模块
使用账号密码进行登录，支持验证码自动识别
"""
import os
import sys
import time
import json
import base64
import logging
from logging.handlers import RotatingFileHandler
from DrissionPage import ChromiumPage, ChromiumOptions

# 添加backend目录到path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)


def setup_password_login_logger():
    """为密码登录模块设置日志"""
    pwd_logger = logging.getLogger(__name__)

    # 避免重复配置
    if pwd_logger.handlers:
        return pwd_logger

    pwd_logger.setLevel(logging.INFO)
    pwd_logger.propagate = False

    # 日志目录
    log_dir = os.path.join(BACKEND_DIR, '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)

    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-5s | PWD_LOGIN| %(name)-20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 写入all.log
    all_log_file = os.path.join(log_dir, 'all.log')
    all_handler = RotatingFileHandler(
        all_log_file,
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    all_handler.setLevel(logging.DEBUG)
    all_handler.setFormatter(formatter)
    pwd_logger.addHandler(all_handler)

    # 写入zhihu日志
    zhihu_log_file = os.path.join(log_dir, 'zhihu.log')
    zhihu_handler = RotatingFileHandler(
        zhihu_log_file,
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    zhihu_handler.setLevel(logging.DEBUG)
    zhihu_handler.setFormatter(formatter)
    pwd_logger.addHandler(zhihu_handler)

    # 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    pwd_logger.addHandler(console_handler)

    return pwd_logger


logger = setup_password_login_logger()


class ZhihuPasswordLogin:
    """知乎密码登录类 - 支持验证码自动识别"""

    def __init__(self, cookies_dir=None):
        """
        初始化密码登录

        Args:
            cookies_dir: Cookie存储目录
        """
        self.driver = None
        self.login_url = 'https://www.zhihu.com/signin'
        self.captcha_service = None

        if cookies_dir is None:
            cookies_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cookies')
        self.cookies_dir = cookies_dir
        os.makedirs(self.cookies_dir, exist_ok=True)

        # 初始化验证码服务
        self._init_captcha_service()

    def _init_captcha_service(self):
        """初始化验证码识别服务"""
        try:
            from services.captcha_service import CaptchaService
            self.captcha_service = CaptchaService()
            if self.captcha_service.token:
                logger.info('✓ 验证码识别服务已初始化')
            else:
                logger.warning('⚠ 验证码服务未配置API密钥')
                self.captcha_service = None
        except Exception as e:
            logger.warning(f'验证码服务初始化失败: {e}')
            self.captcha_service = None

    def init_browser(self, headless=None):
        """
        初始化浏览器（全面反检测）

        Args:
            headless: 是否无头模式，None表示自动检测
        """
        try:
            co = ChromiumOptions()

            # 服务器环境检测
            if headless is None:
                is_server = not os.environ.get('DISPLAY')
            else:
                is_server = headless

            if is_server:
                logger.info("使用headless模式（全面反检测）")
                co.headless(True)
                co.set_argument('--no-sandbox')
                co.set_argument('--disable-dev-shm-usage')
                co.set_argument('--disable-gpu')
                # 使用新版headless模式，更难被检测
                co.set_argument('--headless=new')
            else:
                co.headless(False)

            # ===== 全面反检测配置 =====
            # 禁用自动化特征
            co.set_argument('--disable-blink-features=AutomationControlled')

            # 禁用各种可能暴露自动化的特性
            co.set_argument('--disable-infobars')
            co.set_argument('--disable-extensions')
            co.set_argument('--disable-default-apps')
            co.set_argument('--disable-component-extensions-with-background-pages')
            co.set_argument('--disable-background-networking')
            co.set_argument('--disable-sync')
            co.set_argument('--disable-translate')
            co.set_argument('--disable-features=TranslateUI')
            co.set_argument('--disable-ipc-flooding-protection')
            co.set_argument('--disable-renderer-backgrounding')
            co.set_argument('--disable-backgrounding-occluded-windows')

            # 窗口和显示设置
            co.set_argument('--window-size=1920,1080')
            co.set_argument('--start-maximized')

            # 忽略证书错误
            co.set_argument('--ignore-certificate-errors')
            co.set_argument('--ignore-ssl-errors')

            # 设置语言和地区
            co.set_argument('--lang=zh-CN')
            co.set_argument('--accept-lang=zh-CN,zh;q=0.9,en;q=0.8')

            # 禁用自动化相关的开关
            co.set_argument('--disable-automation')
            co.set_argument('--disable-blink-features')

            # 媒体流设置（模拟真实浏览器）
            co.set_argument('--use-fake-ui-for-media-stream')
            co.set_argument('--use-fake-device-for-media-stream')

            # 设置真实的User-Agent（模拟最新Chrome）
            ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            co.set_user_agent(ua)

            # 设置首选项，进一步隐藏自动化特征
            prefs = {
                'credentials_enable_service': False,
                'profile.password_manager_enabled': False,
                'profile.default_content_setting_values.notifications': 2,
                'excludeSwitches': ['enable-automation'],
                'useAutomationExtension': False
            }

            self.driver = ChromiumPage(addr_or_opts=co)
            logger.info('✓ 密码登录浏览器初始化成功')
            return True
        except Exception as e:
            logger.error(f'浏览器初始化失败: {e}', exc_info=True)
            return False

    def _apply_stealth_js(self):
        """应用全面的反检测JavaScript"""
        try:
            stealth_js = """
            // ===== 1. 隐藏webdriver特征 =====
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
                configurable: true
            });

            // 删除webdriver相关属性
            delete navigator.__proto__.webdriver;

            // ===== 2. 模拟真实的plugins =====
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    const plugins = [
                        {
                            name: 'Chrome PDF Plugin',
                            description: 'Portable Document Format',
                            filename: 'internal-pdf-viewer',
                            length: 1
                        },
                        {
                            name: 'Chrome PDF Viewer',
                            description: '',
                            filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai',
                            length: 1
                        },
                        {
                            name: 'Native Client',
                            description: '',
                            filename: 'internal-nacl-plugin',
                            length: 2
                        }
                    ];
                    plugins.item = (i) => plugins[i] || null;
                    plugins.namedItem = (name) => plugins.find(p => p.name === name) || null;
                    plugins.refresh = () => {};
                    return plugins;
                },
                configurable: true
            });

            // ===== 3. 模拟真实的mimeTypes =====
            Object.defineProperty(navigator, 'mimeTypes', {
                get: () => {
                    const mimeTypes = [
                        { type: 'application/pdf', suffixes: 'pdf', description: 'Portable Document Format' },
                        { type: 'application/x-google-chrome-pdf', suffixes: 'pdf', description: 'Portable Document Format' }
                    ];
                    mimeTypes.item = (i) => mimeTypes[i] || null;
                    mimeTypes.namedItem = (name) => mimeTypes.find(m => m.type === name) || null;
                    return mimeTypes;
                },
                configurable: true
            });

            // ===== 4. 设置languages =====
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en-US', 'en'],
                configurable: true
            });

            Object.defineProperty(navigator, 'language', {
                get: () => 'zh-CN',
                configurable: true
            });

            // ===== 5. 设置platform =====
            Object.defineProperty(navigator, 'platform', {
                get: () => 'Win32',
                configurable: true
            });

            // ===== 6. 设置hardwareConcurrency =====
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 8,
                configurable: true
            });

            // ===== 7. 设置deviceMemory =====
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => 8,
                configurable: true
            });

            // ===== 8. 模拟Chrome对象 =====
            window.chrome = {
                runtime: {
                    connect: function() {},
                    sendMessage: function() {},
                    onMessage: { addListener: function() {} },
                    onConnect: { addListener: function() {} },
                    id: undefined
                },
                loadTimes: function() {
                    return {
                        commitLoadTime: Date.now() / 1000 - 0.5,
                        connectionInfo: 'http/1.1',
                        finishDocumentLoadTime: Date.now() / 1000 - 0.1,
                        finishLoadTime: Date.now() / 1000,
                        firstPaintAfterLoadTime: 0,
                        firstPaintTime: Date.now() / 1000 - 0.3,
                        navigationType: 'Other',
                        npnNegotiatedProtocol: 'unknown',
                        requestTime: Date.now() / 1000 - 1,
                        startLoadTime: Date.now() / 1000 - 0.8,
                        wasAlternateProtocolAvailable: false,
                        wasFetchedViaSpdy: false,
                        wasNpnNegotiated: false
                    };
                },
                csi: function() {
                    return {
                        onloadT: Date.now(),
                        startE: Date.now() - 500,
                        pageT: 500
                    };
                },
                app: {
                    isInstalled: false,
                    InstallState: { DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed' },
                    RunningState: { CANNOT_RUN: 'cannot_run', READY_TO_RUN: 'ready_to_run', RUNNING: 'running' }
                }
            };

            // ===== 9. 修改permissions =====
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = function(parameters) {
                if (parameters.name === 'notifications') {
                    return Promise.resolve({ state: 'prompt', onchange: null });
                }
                return originalQuery.call(this, parameters);
            };

            // ===== 10. 隐藏自动化痕迹 =====
            // 覆盖Function.prototype.toString，隐藏native code修改
            const originalToString = Function.prototype.toString;
            Function.prototype.toString = function() {
                if (this === navigator.permissions.query) {
                    return 'function query() { [native code] }';
                }
                return originalToString.call(this);
            };

            // ===== 11. 设置正确的屏幕属性 =====
            Object.defineProperty(screen, 'width', { get: () => 1920, configurable: true });
            Object.defineProperty(screen, 'height', { get: () => 1080, configurable: true });
            Object.defineProperty(screen, 'availWidth', { get: () => 1920, configurable: true });
            Object.defineProperty(screen, 'availHeight', { get: () => 1040, configurable: true });
            Object.defineProperty(screen, 'colorDepth', { get: () => 24, configurable: true });
            Object.defineProperty(screen, 'pixelDepth', { get: () => 24, configurable: true });

            // ===== 12. WebGL渲染器信息 =====
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                if (parameter === 37446) {
                    return 'Intel Iris OpenGL Engine';
                }
                return getParameter.call(this, parameter);
            };

            // ===== 13. 隐藏Headless特征 =====
            Object.defineProperty(navigator, 'vendor', {
                get: () => 'Google Inc.',
                configurable: true
            });

            Object.defineProperty(navigator, 'appVersion', {
                get: () => '5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                configurable: true
            });

            // ===== 14. 覆盖getter检测 =====
            const elementDescriptor = Object.getOwnPropertyDescriptor(HTMLElement.prototype, 'offsetHeight');
            Object.defineProperty(HTMLDivElement.prototype, 'offsetHeight', {
                ...elementDescriptor,
                get: function() {
                    if (this.id === 'modernizr') {
                        return 1;
                    }
                    return elementDescriptor.get.apply(this);
                },
            });

            console.log('Stealth mode activated');
            """
            self.driver.run_js(stealth_js)
            logger.debug('✓ 全面反检测JS已应用')
        except Exception as e:
            logger.warning(f'应用反检测JS失败: {e}')

    def _handle_unhuman_check(self, max_retries=3):
        """
        处理知乎人机验证页面（增强版）

        Args:
            max_retries: 最大重试次数

        Returns:
            bool: 是否处理成功
        """
        try:
            logger.info('='*50)
            logger.info('开始处理知乎人机验证(unhuman)页面')
            logger.info('='*50)

            # 首先等待页面加载
            time.sleep(3)

            # 应用反检测JS
            self._apply_stealth_js()

            for retry in range(max_retries):
                logger.info(f'人机验证处理 - 第 {retry + 1}/{max_retries} 次尝试')

                # 检查是否已经通过验证
                current_url = self.driver.url
                if 'unhuman' not in current_url:
                    logger.info('✓ 人机验证已通过（URL已改变）')
                    return True

                # 保存截图用于调试
                try:
                    screenshot_path = f'/tmp/zhihu_unhuman_{retry}.png'
                    self.driver.get_screenshot(screenshot_path)
                    logger.info(f'截图已保存: {screenshot_path}')
                except:
                    pass

                # 知乎的unhuman页面通常使用网易易盾验证码
                # 尝试多种检测方式
                captcha_handled = False

                # 1. 尝试检测并处理滑块验证码
                slide_selectors = [
                    '.yidun_slider',
                    '.yidun_slide_button',
                    '.yidun--light .yidun_slider',
                    '[class*="yidun"][class*="slider"]',
                    '.nc-lang-cnt .nc_iconfont',
                    '.captcha-slider',
                    '.slider-btn',
                ]

                for selector in slide_selectors:
                    try:
                        slide_element = self.driver.ele(selector, timeout=2)
                        if slide_element:
                            logger.info(f'找到滑块元素: {selector}')
                            success, msg = self._handle_yidun_slide_captcha()
                            if success:
                                captcha_handled = True
                                break
                    except:
                        continue

                if captcha_handled:
                    time.sleep(3)
                    if 'unhuman' not in self.driver.url:
                        logger.info('✓ 滑块验证通过')
                        return True
                    else:
                        logger.warning('滑块验证后仍在unhuman页面，继续重试')
                        continue

                # 2. 尝试检测点击验证（如果有的话）
                click_selectors = [
                    '.yidun_bgimg',
                    '.yidun_bg-img',
                    '[class*="yidun"][class*="bg"]',
                ]

                for selector in click_selectors:
                    try:
                        click_element = self.driver.ele(selector, timeout=2)
                        if click_element:
                            logger.info(f'找到点选验证码: {selector}')
                            # 尝试点选验证码
                            success, msg = self._handle_click_captcha(click_element)
                            if success:
                                captcha_handled = True
                                break
                    except:
                        continue

                if captcha_handled:
                    time.sleep(3)
                    if 'unhuman' not in self.driver.url:
                        logger.info('✓ 点选验证通过')
                        return True

                # 3. 尝试简单等待（有时验证会自动通过）
                logger.info('等待验证自动完成...')
                for _ in range(5):
                    time.sleep(2)
                    if 'unhuman' not in self.driver.url:
                        logger.info('✓ 验证自动通过')
                        return True

                # 4. 尝试刷新页面重试
                if retry < max_retries - 1:
                    logger.info('刷新页面重试...')
                    self.driver.refresh()
                    time.sleep(3)
                    self._apply_stealth_js()

            logger.error('人机验证失败，服务器IP可能被知乎限制')
            logger.error('建议：1.更换服务器IP 2.使用代理 3.等待一段时间后重试')
            return False

        except Exception as e:
            logger.error(f'处理人机验证失败: {e}', exc_info=True)
            return False

    def _handle_yidun_slide_captcha(self):
        """
        专门处理网易易盾滑块验证码

        Returns:
            (success, message)
        """
        try:
            logger.info('开始处理网易易盾滑块验证码...')

            # 等待验证码完全加载
            time.sleep(2)

            # 获取滑块和背景图
            bg_selectors = [
                '.yidun_bg-img img',
                '.yidun_bgimg img',
                'img.yidun_bg-img',
                '.yidun_panel img[src*="bg"]',
            ]

            slide_selectors = [
                '.yidun_jigsaw img',
                'img.yidun_jigsaw',
                '.yidun_panel img[src*="front"]',
            ]

            slider_btn_selectors = [
                '.yidun_slider__icon',
                '.yidun_slider .yidun_control',
                '.yidun_slide_button',
                '[class*="yidun"][class*="slider"]',
            ]

            bg_img = None
            slide_img = None
            slider_btn = None

            # 查找背景图
            for selector in bg_selectors:
                try:
                    bg_img = self.driver.ele(selector, timeout=2)
                    if bg_img:
                        logger.info(f'找到背景图: {selector}')
                        break
                except:
                    continue

            # 查找滑块图
            for selector in slide_selectors:
                try:
                    slide_img = self.driver.ele(selector, timeout=2)
                    if slide_img:
                        logger.info(f'找到滑块图: {selector}')
                        break
                except:
                    continue

            # 查找滑块按钮
            for selector in slider_btn_selectors:
                try:
                    slider_btn = self.driver.ele(selector, timeout=2)
                    if slider_btn:
                        logger.info(f'找到滑块按钮: {selector}')
                        break
                except:
                    continue

            if not slider_btn:
                logger.warning('未找到滑块按钮，尝试简单滑动')
                # 尝试找任何可滑动的元素
                slider_btn = self.driver.ele('.yidun_slider', timeout=2)
                if not slider_btn:
                    return False, '未找到滑块元素'

            # 尝试使用验证码服务识别滑动距离
            if self.captcha_service and bg_img and slide_img:
                try:
                    bg_src = bg_img.attr('src')
                    slide_src = slide_img.attr('src')

                    if bg_src and slide_src:
                        bg_bytes = self._get_image_bytes(bg_src)
                        slide_bytes = self._get_image_bytes(slide_src)

                        if bg_bytes and slide_bytes:
                            success, distance, _ = self.captcha_service.recognize_slide(
                                slide_image_bytes=slide_bytes,
                                background_image_bytes=bg_bytes
                            )

                            if success and distance:
                                logger.info(f'✓ 识别滑动距离: {distance}px')
                                return self._perform_human_like_slide(slider_btn, int(distance))
                except Exception as e:
                    logger.warning(f'验证码服务识别失败: {e}')

            # 如果验证码服务失败，使用智能滑动策略
            logger.info('使用智能滑动策略...')
            return self._smart_slide(slider_btn)

        except Exception as e:
            logger.error(f'处理易盾滑块失败: {e}', exc_info=True)
            return False, str(e)

    def _smart_slide(self, slider_btn):
        """
        智能滑动策略 - 模拟人类行为

        Args:
            slider_btn: 滑块按钮元素

        Returns:
            (success, message)
        """
        import random

        try:
            # 常见的滑块验证码距离范围是 200-280 像素
            # 多次尝试不同的距离
            distances = [260, 240, 270, 250, 230]

            for attempt, base_distance in enumerate(distances):
                logger.info(f'智能滑动尝试 {attempt + 1}/5, 基础距离: {base_distance}px')

                # 添加随机偏移
                distance = base_distance + random.randint(-10, 10)

                success, msg = self._perform_human_like_slide(slider_btn, distance)

                if success:
                    time.sleep(2)
                    # 检查是否通过
                    if 'unhuman' not in self.driver.url:
                        return True, '滑动验证通过'

                    # 检查是否有成功提示
                    try:
                        success_indicator = self.driver.ele('.yidun_tips__text', timeout=1)
                        if success_indicator and '成功' in success_indicator.text:
                            time.sleep(2)
                            return True, '滑动验证通过'
                    except:
                        pass

                # 等待后重试
                time.sleep(1)

            return False, '智能滑动未能通过验证'

        except Exception as e:
            logger.error(f'智能滑动失败: {e}')
            return False, str(e)

    def _perform_human_like_slide(self, slider_btn, distance):
        """
        执行模拟人类行为的滑动

        Args:
            slider_btn: 滑块按钮元素
            distance: 滑动距离

        Returns:
            (success, message)
        """
        import random
        import math

        try:
            actions = self.driver.actions

            # 先移动到滑块位置
            actions.move_to(slider_btn)
            time.sleep(random.uniform(0.1, 0.3))

            # 按住滑块
            actions.hold(slider_btn)
            time.sleep(random.uniform(0.1, 0.2))

            # 生成人类样式的滑动轨迹
            track = self._generate_human_track(distance)

            # 执行滑动
            current_x = 0
            for move_x, move_y, delay in track:
                actions.move(move_x, move_y)
                current_x += move_x
                time.sleep(delay)

            # 释放
            time.sleep(random.uniform(0.05, 0.1))
            actions.release()
            time.sleep(0.5)

            logger.info(f'✓ 人类样式滑动完成，实际滑动: {current_x}px')
            return True, '滑动完成'

        except Exception as e:
            logger.error(f'人类样式滑动失败: {e}')
            return False, str(e)

    def _generate_human_track(self, distance):
        """
        生成模拟人类的滑动轨迹

        Args:
            distance: 总滑动距离

        Returns:
            轨迹列表 [(x, y, delay), ...]
        """
        import random
        import math

        track = []
        current = 0

        # 缓动函数 - 开始快，中间慢，结束快
        # 添加一些随机性
        mid_point = distance * random.uniform(0.6, 0.8)

        while current < distance:
            if current < mid_point:
                # 加速阶段
                move = random.randint(10, 25)
            else:
                # 减速阶段
                remaining = distance - current
                if remaining > 20:
                    move = random.randint(5, 15)
                else:
                    move = random.randint(2, 8)

            if current + move > distance:
                move = distance - current

            # Y轴添加微小抖动
            y_move = random.randint(-2, 2)

            # 随机延迟
            delay = random.uniform(0.01, 0.03)

            track.append((move, y_move, delay))
            current += move

        # 添加一些回弹
        if random.random() > 0.5:
            track.append((random.randint(2, 5), 0, 0.05))
            track.append((-random.randint(2, 5), 0, 0.05))

        return track

    def _detect_captcha(self):
        """
        检测页面是否有验证码

        Returns:
            (has_captcha, captcha_type, captcha_element)
            captcha_type: 'image'=图片验证码, 'slide'=滑块验证码, 'click'=点选验证码
        """
        try:
            # 检测图片验证码
            image_captcha_selectors = [
                'img.Captcha-englishImg',
                'img[alt*="验证码"]',
                '.Captcha img',
                'img[src*="captcha"]',
            ]

            for selector in image_captcha_selectors:
                try:
                    captcha_img = self.driver.ele(selector, timeout=1)
                    if captcha_img:
                        logger.info(f'检测到图片验证码: {selector}')
                        return True, 'image', captcha_img
                except:
                    continue

            # 检测滑块验证码
            slide_captcha_selectors = [
                '.yidun_slider',
                '.geetest_slider_button',
                '.nc_wrapper',
                '[class*="slide"]',
                '.captcha-slider',
            ]

            for selector in slide_captcha_selectors:
                try:
                    slide_element = self.driver.ele(selector, timeout=1)
                    if slide_element:
                        logger.info(f'检测到滑块验证码: {selector}')
                        return True, 'slide', slide_element
                except:
                    continue

            # 检测点选验证码
            click_captcha_selectors = [
                '.yidun_bgimg',
                '.geetest_item_img',
                '[class*="click-captcha"]',
            ]

            for selector in click_captcha_selectors:
                try:
                    click_element = self.driver.ele(selector, timeout=1)
                    if click_element:
                        logger.info(f'检测到点选验证码: {selector}')
                        return True, 'click', click_element
                except:
                    continue

            return False, None, None

        except Exception as e:
            logger.debug(f'验证码检测异常: {e}')
            return False, None, None

    def _handle_image_captcha(self, captcha_img):
        """
        处理图片验证码

        Args:
            captcha_img: 验证码图片元素

        Returns:
            (success, message)
        """
        if not self.captcha_service:
            logger.error('验证码服务未初始化，无法自动识别')
            return False, '验证码服务未配置'

        try:
            # 获取验证码图片
            img_src = captcha_img.attr('src')

            if img_src.startswith('data:image'):
                # base64格式的图片
                base64_data = img_src.split(',')[1]
                image_bytes = base64.b64decode(base64_data)
            else:
                # URL格式，需要下载
                import requests
                resp = requests.get(img_src, timeout=10)
                image_bytes = resp.content

            # 调用验证码识别服务
            logger.info('正在识别图片验证码...')
            success, result, data = self.captcha_service.recognize_common(
                image_bytes=image_bytes
            )

            if not success:
                logger.error(f'验证码识别失败: {result}')
                return False, f'验证码识别失败: {result}'

            logger.info(f'✓ 验证码识别成功: {result}')

            # 找到验证码输入框并输入
            captcha_input_selectors = [
                'input[name="captcha"]',
                'input[placeholder*="验证码"]',
                '.Captcha input',
                'input.Input[name*="captcha"]',
            ]

            captcha_input = None
            for selector in captcha_input_selectors:
                try:
                    captcha_input = self.driver.ele(selector, timeout=2)
                    if captcha_input:
                        break
                except:
                    continue

            if not captcha_input:
                logger.error('未找到验证码输入框')
                return False, '未找到验证码输入框'

            captcha_input.clear()
            captcha_input.input(result)
            logger.info('✓ 验证码已输入')

            return True, '验证码识别成功'

        except Exception as e:
            logger.error(f'处理图片验证码失败: {e}', exc_info=True)
            return False, str(e)

    def _handle_slide_captcha(self, slide_element):
        """
        处理滑块验证码

        Args:
            slide_element: 滑块元素

        Returns:
            (success, message)
        """
        if not self.captcha_service:
            logger.error('验证码服务未初始化')
            return False, '验证码服务未配置'

        try:
            # 获取滑块验证码的背景图和滑块图
            # 不同验证码厂商的元素结构不同，需要适配

            # 尝试获取网易易盾验证码图片
            bg_selectors = ['.yidun_bg-img', '.yidun_bgimg img', '.geetest_canvas_bg']
            slide_selectors = ['.yidun_jigsaw', '.yidun_slice img', '.geetest_canvas_slice']

            bg_img = None
            slide_img = None

            for selector in bg_selectors:
                try:
                    bg_img = self.driver.ele(selector, timeout=1)
                    if bg_img:
                        break
                except:
                    continue

            for selector in slide_selectors:
                try:
                    slide_img = self.driver.ele(selector, timeout=1)
                    if slide_img:
                        break
                except:
                    continue

            if not bg_img or not slide_img:
                logger.warning('未找到滑块验证码图片元素，尝试简单滑动')
                # 简单滑动策略
                return self._simple_slide(slide_element)

            # 获取图片数据
            bg_src = bg_img.attr('src')
            slide_src = slide_img.attr('src')

            bg_bytes = self._get_image_bytes(bg_src)
            slide_bytes = self._get_image_bytes(slide_src)

            if not bg_bytes or not slide_bytes:
                return self._simple_slide(slide_element)

            # 调用滑块识别API
            success, distance, data = self.captcha_service.recognize_slide(
                slide_image_bytes=slide_bytes,
                background_image_bytes=bg_bytes
            )

            if not success:
                logger.warning(f'滑块识别失败: {data}, 尝试简单滑动')
                return self._simple_slide(slide_element)

            logger.info(f'✓ 滑块距离识别成功: {distance}px')

            # 执行滑动
            return self._perform_slide(slide_element, distance)

        except Exception as e:
            logger.error(f'处理滑块验证码失败: {e}', exc_info=True)
            return self._simple_slide(slide_element)

    def _get_image_bytes(self, src):
        """获取图片二进制数据"""
        try:
            if src.startswith('data:image'):
                base64_data = src.split(',')[1]
                return base64.b64decode(base64_data)
            else:
                import requests
                resp = requests.get(src, timeout=10)
                return resp.content
        except Exception as e:
            logger.error(f'获取图片失败: {e}')
            return None

    def _simple_slide(self, slide_element):
        """简单滑动策略（用于识别失败时的fallback）"""
        try:
            # 模拟人工滑动
            import random

            # 获取滑块位置和大小
            actions = self.driver.actions

            # 滑动到末端（大约260-280像素是常见的滑块距离）
            distance = random.randint(250, 280)

            # 按住滑块
            actions.hold(slide_element)
            time.sleep(0.1)

            # 分段滑动，模拟人工操作
            moved = 0
            while moved < distance:
                step = random.randint(10, 30)
                if moved + step > distance:
                    step = distance - moved
                actions.move(step, random.randint(-2, 2))
                moved += step
                time.sleep(random.uniform(0.01, 0.03))

            # 释放
            actions.release()
            time.sleep(1)

            logger.info(f'✓ 简单滑动完成，滑动距离: {distance}px')
            return True, '滑动完成'

        except Exception as e:
            logger.error(f'简单滑动失败: {e}')
            return False, str(e)

    def _perform_slide(self, slide_element, distance):
        """执行精确滑动"""
        try:
            import random

            actions = self.driver.actions

            # 按住滑块
            actions.hold(slide_element)
            time.sleep(0.1)

            # 分段滑动，模拟人工轨迹
            moved = 0
            while moved < distance:
                # 开始快，中间慢，结束快
                if moved < distance * 0.3:
                    step = random.randint(15, 25)
                elif moved < distance * 0.7:
                    step = random.randint(5, 15)
                else:
                    step = random.randint(10, 20)

                if moved + step > distance:
                    step = distance - moved

                # 添加微小的Y轴偏移
                actions.move(step, random.randint(-1, 1))
                moved += step
                time.sleep(random.uniform(0.01, 0.02))

            # 稍微过头再回来
            actions.move(3, 0)
            time.sleep(0.05)
            actions.move(-3, 0)

            # 释放
            actions.release()
            time.sleep(1)

            logger.info(f'✓ 精确滑动完成，目标距离: {distance}px')
            return True, '滑动完成'

        except Exception as e:
            logger.error(f'精确滑动失败: {e}')
            return False, str(e)

    def _handle_click_captcha(self, click_element):
        """
        处理点选验证码

        Args:
            click_element: 点选验证码元素

        Returns:
            (success, message)
        """
        if not self.captcha_service:
            return False, '验证码服务未配置'

        try:
            # 获取验证码图片
            img_src = click_element.attr('src')
            if not img_src:
                # 尝试获取背景图
                style = click_element.attr('style')
                if style and 'url(' in style:
                    import re
                    match = re.search(r'url\(["\']?([^"\']+)["\']?\)', style)
                    if match:
                        img_src = match.group(1)

            if not img_src:
                return False, '未找到点选验证码图片'

            image_bytes = self._get_image_bytes(img_src)
            if not image_bytes:
                return False, '获取点选验证码图片失败'

            # 获取提示文字
            hint_selectors = ['.yidun_tips__text', '.geetest_tip_content', '[class*="tip"]']
            hint_text = ''
            for selector in hint_selectors:
                try:
                    hint_element = self.driver.ele(selector, timeout=1)
                    if hint_element:
                        hint_text = hint_element.text
                        break
                except:
                    continue

            # 调用点选识别API
            success, coordinates, data = self.captcha_service.recognize_click(
                image_bytes=image_bytes,
                extra=hint_text
            )

            if not success:
                return False, f'点选识别失败: {data}'

            logger.info(f'✓ 点选坐标识别成功: {coordinates}')

            # 执行点击
            for x, y in coordinates:
                click_element.click(x, y)
                time.sleep(0.3)

            time.sleep(1)
            return True, '点选完成'

        except Exception as e:
            logger.error(f'处理点选验证码失败: {e}', exc_info=True)
            return False, str(e)

    def login(self, username, password, max_captcha_retries=3, max_login_retries=3):
        """
        使用账号密码登录（带整体重试机制）

        Args:
            username: 用户名/手机号/邮箱
            password: 密码
            max_captcha_retries: 验证码最大重试次数
            max_login_retries: 整个登录流程最大重试次数

        Returns:
            (success, message, cookies)
        """
        last_error = None

        for login_attempt in range(max_login_retries):
            try:
                logger.info('='*60)
                logger.info(f'开始知乎密码登录流程 (第{login_attempt + 1}/{max_login_retries}次尝试)')
                logger.info(f'账号: {username[:3]}***{username[-4:] if len(username) > 7 else "****"}')
                logger.info('='*60)

                # 如果是重试，先刷新页面
                if login_attempt > 0:
                    logger.info('刷新页面重新开始登录流程...')
                    try:
                        self.driver.refresh()
                        time.sleep(3)
                    except:
                        pass

                if not self.driver:
                    logger.info('[步骤1/7] 初始化浏览器...')
                    if not self.init_browser():
                        logger.error('浏览器初始化失败')
                        last_error = '浏览器初始化失败'
                        continue
                    logger.info('✓ 浏览器初始化成功')

                # 先访问知乎首页，建立session
                logger.info('[步骤2/7] 访问知乎首页建立session...')
                self.driver.get('https://www.zhihu.com/')
                time.sleep(2)
                logger.info(f'  当前URL: {self.driver.url}')

                # 应用反检测JS
                logger.info('[步骤3/7] 应用反检测JS...')
                self._apply_stealth_js()

                # 访问登录页面
                logger.info('[步骤4/7] 访问知乎登录页面...')
                self.driver.get(self.login_url)
                time.sleep(3)

                # 检查是否被重定向到人机验证页面
                current_url = self.driver.url
                logger.info(f'  当前URL: {current_url}')

                if 'unhuman' in current_url:
                    logger.warning('⚠ 检测到人机验证页面(unhuman)，尝试处理...')
                    if not self._handle_unhuman_check():
                        logger.error('✗ 人机验证失败，服务器IP可能被知乎限制')
                        last_error = '人机验证失败，服务器IP可能被知乎限制'
                        # 人机验证失败是致命错误，不再重试
                        return False, last_error, None
                    logger.info('✓ 人机验证通过，重新访问登录页')
                    # 重新访问登录页
                    self.driver.get(self.login_url)
                    time.sleep(3)
                    logger.info(f'  当前URL: {self.driver.url}')

                # 切换到密码登录
                logger.info('[步骤5/7] 切换到密码登录模式...')
                if not self._switch_to_password_login():
                    logger.warning('切换密码登录模式失败，尝试继续...')

                # 输入用户名
                logger.info('[步骤6/7] 输入账号密码...')
                if not self._input_username(username):
                    logger.error('✗ 未找到用户名输入框，刷新页面重试')
                    last_error = '未找到用户名输入框'
                    continue
                logger.info('  ✓ 用户名已输入')

                # 输入密码
                if not self._input_password(password):
                    logger.error('✗ 未找到密码输入框，刷新页面重试')
                    last_error = '未找到密码输入框'
                    continue
                logger.info('  ✓ 密码已输入')

                # 点击登录按钮
                logger.info('[步骤7/7] 点击登录按钮...')
                if not self._click_login_button():
                    logger.error('✗ 未找到登录按钮，刷新页面重试')
                    last_error = '未找到登录按钮'
                    continue

                # 等待页面响应
                logger.info('等待页面响应...')
                time.sleep(3)
                logger.info(f'  当前URL: {self.driver.url}')

                # 处理验证码（带重试）
                captcha_retry = 0
                while captcha_retry < max_captcha_retries:
                    has_captcha, captcha_type, captcha_element = self._detect_captcha()

                    if not has_captcha:
                        logger.info('未检测到验证码，继续...')
                        break

                    logger.info(f'检测到验证码 (类型: {captcha_type})，第{captcha_retry + 1}/{max_captcha_retries}次尝试处理...')

                    if captcha_type == 'image':
                        success, msg = self._handle_image_captcha(captcha_element)
                    elif captcha_type == 'slide':
                        success, msg = self._handle_slide_captcha(captcha_element)
                    elif captcha_type == 'click':
                        success, msg = self._handle_click_captcha(captcha_element)
                    else:
                        success = False
                        msg = f'不支持的验证码类型: {captcha_type}'

                    if not success:
                        logger.warning(f'验证码处理失败: {msg}')
                        captcha_retry += 1
                        # 刷新验证码
                        self._refresh_captcha()
                        time.sleep(2)
                        continue

                    logger.info('✓ 验证码处理成功，重新点击登录')
                    # 验证码处理成功，重新点击登录
                    time.sleep(1)
                    self._click_login_button()
                    time.sleep(3)

                    captcha_retry += 1

                # 等待登录完成
                logger.info('等待登录完成...')
                time.sleep(3)

                # 验证登录
                logger.info('验证登录状态...')
                current_url = self.driver.url
                logger.info(f'  当前URL: {current_url}')

                if self.verify_login():
                    logger.info('='*60)
                    logger.info('✓✓✓ 密码登录成功！')
                    logger.info('='*60)
                    cookies = self.get_cookies()
                    logger.info(f'获取到 {len(cookies)} 个Cookie')
                    return True, '登录成功', cookies
                else:
                    # 检查是否还有验证码
                    has_captcha, _, _ = self._detect_captcha()
                    if has_captcha:
                        logger.warning('登录失败：验证码未通过，刷新页面重试')
                        last_error = '验证码识别失败'
                        continue

                    # 检查是否有错误提示
                    error_msg = self._get_login_error_message()
                    if error_msg:
                        logger.error(f'登录失败：{error_msg}')
                        # 如果是账号密码错误，不再重试
                        if '密码' in error_msg or '账号' in error_msg:
                            return False, error_msg, None
                        last_error = error_msg
                        continue

                    logger.warning('登录状态验证失败，刷新页面重试')
                    last_error = '登录失败，请检查账号密码是否正确'
                    continue

            except Exception as e:
                logger.error(f'密码登录异常: {e}', exc_info=True)
                last_error = str(e)
                # 异常时尝试刷新页面
                try:
                    logger.info('登录异常，尝试刷新页面...')
                    self.driver.refresh()
                    time.sleep(2)
                except:
                    pass
                continue

        # 所有重试都失败
        logger.error(f'密码登录失败，已重试{max_login_retries}次')
        return False, last_error or '登录失败', None

    def _get_login_error_message(self):
        """获取登录页面的错误提示信息"""
        try:
            error_selectors = [
                '.Notification-textSection',
                '.SignFlow-errorMessage',
                '.ErrorMessage',
                '.Login-errorMessage',
                '[class*="error"]',
            ]

            for selector in error_selectors:
                try:
                    error_element = self.driver.ele(selector, timeout=1)
                    if error_element and error_element.text:
                        return error_element.text.strip()
                except:
                    continue
            return None
        except:
            return None

    def _switch_to_password_login(self):
        """切换到密码登录标签"""
        try:
            password_tab_selectors = [
                'text:密码登录',
                'text:账号密码登录',
                '.SignFlow-accountTab',
                'div[role="tab"]:has-text("密码登录")',
            ]

            for selector in password_tab_selectors:
                try:
                    tab = self.driver.ele(selector, timeout=2)
                    if tab:
                        logger.info(f'找到密码登录标签: {selector}')
                        tab.click()
                        time.sleep(2)
                        return True
                except:
                    continue
            return False
        except Exception as e:
            logger.warning(f'切换密码登录标签失败: {e}')
            return False

    def _input_username(self, username):
        """输入用户名"""
        username_input_selectors = [
            'input[name="username"]',
            'input[placeholder*="手机号"]',
            'input[placeholder*="邮箱"]',
            '.SignFlow-account input',
            'input.Input',
        ]

        for selector in username_input_selectors:
            try:
                username_input = self.driver.ele(selector, timeout=2)
                if username_input:
                    logger.info(f'找到用户名输入框: {selector}')
                    username_input.clear()
                    username_input.input(username)
                    time.sleep(0.5)
                    return True
            except:
                continue
        return False

    def _input_password(self, password):
        """输入密码"""
        password_input_selectors = [
            'input[type="password"]',
            'input[name="password"]',
            '.SignFlow-password input',
        ]

        for selector in password_input_selectors:
            try:
                password_input = self.driver.ele(selector, timeout=2)
                if password_input:
                    logger.info(f'找到密码输入框: {selector}')
                    password_input.clear()
                    password_input.input(password)
                    time.sleep(0.5)
                    return True
            except:
                continue
        return False

    def _click_login_button(self):
        """点击登录按钮"""
        login_btn_selectors = [
            'button:text("登录")',
            'button[type="submit"]',
            '.SignFlow-submitButton',
            'button.Button--primary',
        ]

        for selector in login_btn_selectors:
            try:
                login_btn = self.driver.ele(selector, timeout=2)
                if login_btn:
                    logger.info(f'找到登录按钮: {selector}')
                    login_btn.click()
                    logger.info('✓ 点击登录按钮')
                    return True
            except:
                continue
        return False

    def _refresh_captcha(self):
        """刷新验证码"""
        try:
            refresh_selectors = [
                '.Captcha-refresh',
                'text:看不清',
                'text:换一张',
                '[class*="refresh"]',
            ]

            for selector in refresh_selectors:
                try:
                    refresh_btn = self.driver.ele(selector, timeout=1)
                    if refresh_btn:
                        refresh_btn.click()
                        logger.info('✓ 已刷新验证码')
                        return True
                except:
                    continue
            return False
        except:
            return False

    def verify_login(self):
        """验证是否已登录"""
        try:
            current_url = self.driver.url

            # 如果跳转离开登录页，说明登录成功
            if 'zhihu.com' in current_url and '/signin' not in current_url:
                return True

            # 检查页面内容
            page_html = self.driver.html
            if any(indicator in page_html for indicator in ['我的主页', '退出登录', '个人中心', '创作中心']):
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
                cookies = []
                for cookie in self.driver.cookies():
                    cookies.append({
                        'name': cookie.get('name'),
                        'value': cookie.get('value'),
                        'domain': cookie.get('domain', '.zhihu.com'),
                        'path': cookie.get('path', '/'),
                    })
                return cookies
            return []
        except Exception as e:
            logger.error(f'获取Cookie失败: {e}')
            return []

    def save_cookies(self, username):
        """
        保存Cookie到文件

        Args:
            username: 用户名（用于文件命名）
        """
        try:
            cookies = self.get_cookies()
            if not cookies:
                logger.warning('没有Cookie可保存')
                return False

            cookie_file = os.path.join(self.cookies_dir, f'zhihu_{username}.json')
            with open(cookie_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)

            logger.info(f'✓ Cookie已保存: {cookie_file}')
            return True
        except Exception as e:
            logger.error(f'保存Cookie失败: {e}')
            return False

    def close(self):
        """关闭浏览器"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                logger.info('浏览器已关闭')
        except Exception as e:
            logger.warning(f'关闭浏览器时出错: {e}')


# 便捷函数
def zhihu_password_login(username, password, save_cookie=True):
    """
    知乎密码登录便捷函数

    Args:
        username: 用户名
        password: 密码
        save_cookie: 是否保存Cookie

    Returns:
        (success, message, cookies)
    """
    login = ZhihuPasswordLogin()
    try:
        success, message, cookies = login.login(username, password)

        if success and save_cookie:
            login.save_cookies(username)

        return success, message, cookies
    finally:
        login.close()
