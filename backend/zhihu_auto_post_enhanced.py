#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知乎自动发帖模块（增强版）
支持Cookie登录和自动密码登录fallback
"""
import time
import logging
import json
import os
import sys
from logging.handlers import RotatingFileHandler

# 添加backend目录到path以便导入logger_config
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BACKEND_DIR)

def setup_zhihu_logger():
    """为知乎模块设置日志，确保日志写入到logs目录"""
    zhihu_logger = logging.getLogger(__name__)

    # 避免重复配置
    if zhihu_logger.handlers:
        return zhihu_logger

    zhihu_logger.setLevel(logging.INFO)
    zhihu_logger.propagate = False

    # 日志目录
    log_dir = os.path.join(BACKEND_DIR, '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)

    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-5s | ZHIHU    | %(name)-20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 写入all.log
    all_log_file = os.path.join(log_dir, 'all.log')
    all_handler = RotatingFileHandler(
        all_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    all_handler.setLevel(logging.DEBUG)
    all_handler.setFormatter(formatter)
    zhihu_logger.addHandler(all_handler)

    # 写入zhihu专属日志
    zhihu_log_file = os.path.join(log_dir, 'zhihu.log')
    zhihu_handler = RotatingFileHandler(
        zhihu_log_file,
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    zhihu_handler.setLevel(logging.DEBUG)
    zhihu_handler.setFormatter(formatter)
    zhihu_logger.addHandler(zhihu_handler)

    # 同时输出到控制台
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    zhihu_logger.addHandler(console_handler)

    return zhihu_logger

# 初始化logger
logger = setup_zhihu_logger()

class ZhihuAutoPost:
    """知乎自动发帖"""

    def __init__(self, mode='drission'):
        self.mode = mode
        self.page = None
        self.is_logged_in = False

    def init_browser(self):
        """初始化浏览器（增强反检测版本）"""
        try:
            from DrissionPage import ChromiumPage, ChromiumOptions
            import random
            co = ChromiumOptions()

            # 服务器环境检测：如果没有显示器则使用headless模式
            import os
            is_server = not os.environ.get('DISPLAY')
            import shutil
            # 明确指定Chrome浏览器路径（修复DrissionPage找不到chrome的问题）
            chrome_path = shutil.which("google-chrome") or shutil.which("chrome") or "/usr/bin/google-chrome"
            co.set_browser_path(chrome_path)
            logger.info(f"使用Chrome路径: {chrome_path}")

            # ========== 核心反检测配置 ==========
            # 1. 禁用自动化标识
            co.set_argument('--disable-blink-features=AutomationControlled')
            co.set_argument('--disable-automation')
            co.set_argument('--disable-infobars')

            # 2. 禁用WebDriver标识
            co.set_argument('--disable-web-security')
            co.set_argument('--allow-running-insecure-content')

            # 3. 随机化User-Agent（模拟真实浏览器）
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            ]
            selected_ua = random.choice(user_agents)
            co.set_user_agent(selected_ua)
            logger.info(f"使用User-Agent: {selected_ua[:60]}...")

            # 4. 设置真实的窗口大小（避免被检测为无头模式）
            window_sizes = [(1920, 1080), (1366, 768), (1536, 864), (1440, 900)]
            width, height = random.choice(window_sizes)
            co.set_argument(f'--window-size={width},{height}')

            # 5. 禁用可能暴露自动化的特性
            co.set_argument('--disable-extensions')
            co.set_argument('--disable-plugins-discovery')
            co.set_argument('--disable-popup-blocking')
            co.set_argument('--ignore-certificate-errors')
            co.set_argument('--disable-default-apps')

            # 6. 设置语言和时区（模拟中国用户）
            co.set_argument('--lang=zh-CN')
            co.set_argument('--accept-lang=zh-CN,zh;q=0.9,en;q=0.8')

            # 7. 禁用一些可能导致检测的功能
            co.set_argument('--disable-background-networking')
            co.set_argument('--disable-sync')
            co.set_argument('--disable-translate')
            co.set_argument('--metrics-recording-only')
            co.set_argument('--no-first-run')
            co.set_argument('--safebrowsing-disable-auto-update')

            if is_server:
                logger.info("检测到服务器环境，使用新版headless模式")
                # 使用新版headless模式，更难被检测
                co.set_argument('--headless=new')
                co.set_argument('--no-sandbox')
                co.set_argument('--disable-dev-shm-usage')
                co.set_argument('--disable-gpu')
                # 设置虚拟显示尺寸
                co.set_argument('--window-position=0,0')
            else:
                co.headless(False)  # 可见模式,方便调试

            self.page = ChromiumPage(addr_or_opts=co)

            # ========== 注入反检测JavaScript ==========
            self._apply_stealth_js()

            logger.info("✓ 浏览器初始化成功（反检测模式）")
            return True
        except Exception as e:
            logger.error(f"✗ 浏览器初始化失败: {e}", exc_info=True)
            return False

    def _apply_stealth_js(self):
        """注入反检测JavaScript，隐藏自动化特征"""
        stealth_js = """
        // 1. 隐藏webdriver标识
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
            configurable: true
        });

        // 2. 模拟真实的plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => {
                const plugins = [
                    {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format'},
                    {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: ''},
                    {name: 'Native Client', filename: 'internal-nacl-plugin', description: ''}
                ];
                plugins.length = 3;
                return plugins;
            },
            configurable: true
        });

        // 3. 模拟真实的mimeTypes
        Object.defineProperty(navigator, 'mimeTypes', {
            get: () => {
                const mimes = [
                    {type: 'application/pdf', suffixes: 'pdf', description: 'Portable Document Format'},
                    {type: 'application/x-google-chrome-pdf', suffixes: 'pdf', description: 'Portable Document Format'}
                ];
                mimes.length = 2;
                return mimes;
            },
            configurable: true
        });

        // 4. 模拟真实的languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['zh-CN', 'zh', 'en-US', 'en'],
            configurable: true
        });

        // 5. 设置真实的platform
        Object.defineProperty(navigator, 'platform', {
            get: () => 'Win32',
            configurable: true
        });

        // 6. 设置真实的硬件并发数
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 8,
            configurable: true
        });

        // 7. 设置真实的设备内存
        Object.defineProperty(navigator, 'deviceMemory', {
            get: () => 8,
            configurable: true
        });

        // 8. 模拟Chrome运行时对象
        window.chrome = {
            runtime: {
                id: undefined,
                connect: () => {},
                sendMessage: () => {},
                onMessage: { addListener: () => {} }
            },
            loadTimes: () => {},
            csi: () => {},
            app: {}
        };

        // 9. 覆盖权限查询
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );

        // 10. 隐藏Headless特征
        Object.defineProperty(navigator, 'userAgent', {
            get: () => navigator.userAgent.replace('HeadlessChrome', 'Chrome'),
            configurable: true
        });

        // 11. 模拟真实的屏幕属性
        Object.defineProperty(screen, 'width', { get: () => 1920 });
        Object.defineProperty(screen, 'height', { get: () => 1080 });
        Object.defineProperty(screen, 'availWidth', { get: () => 1920 });
        Object.defineProperty(screen, 'availHeight', { get: () => 1040 });
        Object.defineProperty(screen, 'colorDepth', { get: () => 24 });
        Object.defineProperty(screen, 'pixelDepth', { get: () => 24 });

        // 12. 覆盖WebGL渲染器信息
        const getParameterProxyHandler = {
            apply: function(target, thisArg, argumentsList) {
                const param = argumentsList[0];
                const gl = thisArg;
                // UNMASKED_VENDOR_WEBGL
                if (param === 37445) {
                    return 'Intel Inc.';
                }
                // UNMASKED_RENDERER_WEBGL
                if (param === 37446) {
                    return 'Intel Iris OpenGL Engine';
                }
                return Reflect.apply(target, thisArg, argumentsList);
            }
        };

        try {
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            if (gl) {
                gl.getParameter = new Proxy(gl.getParameter.bind(gl), getParameterProxyHandler);
            }
        } catch(e) {}

        // 13. 移除自动化相关的属性
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;

        console.log('Stealth mode activated');
        """
        try:
            self.page.run_js(stealth_js)
            logger.debug("✓ 反检测JavaScript已注入")
        except Exception as e:
            logger.warning(f"⚠ 反检测JavaScript注入失败: {e}")

    def load_cookies(self, username):
        """加载已保存的Cookie"""
        try:
            # 尝试从backend/cookies目录加载
            cookies_dir = os.path.join(os.path.dirname(__file__), 'cookies')
            cookie_file = os.path.join(cookies_dir, f'zhihu_{username}.json')

            if not os.path.exists(cookie_file):
                logger.warning(f"Cookie文件不存在: {cookie_file}")
                return False

            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)

            # 先访问知乎主页
            self.page.get('https://www.zhihu.com')
            time.sleep(1)

            # 每次页面加载后注入反检测JS
            self._apply_stealth_js()

            # 加载Cookie
            for cookie in cookies:
                try:
                    self.page.set.cookies(cookie)
                except Exception as e:
                    logger.debug(f"设置Cookie失败: {cookie.get('name')} - {e}")

            logger.info(f"✓ Cookie加载完成,共{len(cookies)}个")

            # 刷新页面验证登录状态
            self.page.refresh()
            time.sleep(2)

            return self.verify_login()

        except Exception as e:
            logger.error(f"✗ 加载Cookie失败: {e}")
            return False

    def auto_login_with_password(self, username, password):
        """
        使用密码自动登录（当Cookie不存在或失效时的fallback）
        使用新的ZhihuPasswordLogin模块，支持验证码自动识别

        Args:
            username: 知乎账号
            password: 密码

        Returns:
            bool: 是否登录成功
        """
        try:
            logger.info("=" * 60)
            logger.info("开始自动密码登录流程（支持验证码自动识别）")
            logger.info("=" * 60)

            # 使用新的密码登录模块
            try:
                from zhihu_auth.zhihu_password_login import ZhihuPasswordLogin
                logger.info("✓ ZhihuPasswordLogin模块导入成功")
            except ImportError as e:
                logger.error(f"✗ 无法导入ZhihuPasswordLogin模块: {e}")
                return False

            # 创建密码登录实例
            login_handler = ZhihuPasswordLogin()

            try:
                # 执行密码登录（带验证码自动识别）
                logger.info(f"正在使用账号密码登录: {username}")
                success, message, cookies = login_handler.login(username, password)

                if success:
                    logger.info("✓✓ 密码登录成功！")

                    # 保存Cookie
                    logger.info("正在保存登录Cookie...")
                    if login_handler.save_cookies(username):
                        logger.info("✓ Cookie已保存，下次可以直接使用Cookie登录")
                    else:
                        logger.warning("⚠ Cookie保存失败，下次仍需要密码登录")

                    # 关闭登录浏览器
                    login_handler.close()

                    # 重新加载Cookie到DrissionPage发布浏览器
                    logger.info("正在将Cookie加载到发布浏览器...")
                    if self.load_cookies(username):
                        logger.info("✓ Cookie已加载到发布浏览器")
                        return True
                    else:
                        logger.error("✗ Cookie加载到发布浏览器失败")
                        return False
                else:
                    logger.error(f"✗ 密码登录失败: {message}")
                    return False

            finally:
                # 确保关闭登录浏览器
                login_handler.close()

        except Exception as e:
            logger.error(f"✗ 自动登录过程中发生异常: {e}", exc_info=True)
            return False

    def verify_login(self):
        """验证是否已登录"""
        try:
            current_url = self.page.url
            page_html = self.page.html

            # 检查登录标识
            login_indicators = ['我的主页', '退出登录', '个人中心', '创作中心']

            for indicator in login_indicators:
                if indicator in page_html:
                    self.is_logged_in = True
                    logger.info(f"✓✓ 登录验证成功,检测到: {indicator}")
                    return True

            logger.warning("⚠ 未检测到登录标识,可能未登录")
            return False

        except Exception as e:
            logger.error(f"✗ 登录验证失败: {e}")
            return False

    def create_article(self, title, content, topics=None, draft=False):
        """创建文章

        Args:
            title: 文章标题
            content: 文章内容(支持HTML或Markdown)
            topics: 话题列表,如 ['Python', '编程']
            draft: 是否保存为草稿(True)或直接发布(False)
        """
        try:
            if not self.is_logged_in:
                logger.error("未登录,无法发帖")
                return {'success': False, 'message': '未登录'}

            # 访问创作页面
            logger.info("正在进入创作页面...")
            self.page.get('https://zhuanlan.zhihu.com/write')
            time.sleep(2)

            # 每次页面加载后注入反检测JS
            self._apply_stealth_js()
            time.sleep(1)

            # 等待编辑器加载
            logger.info("等待编辑器加载...")
            time.sleep(2)

            # 输入标题
            logger.info("正在输入标题...")
            try:
                title_input = self.page.ele('css:.WriteIndex-titleInput', timeout=5)
                if title_input:
                    title_input.clear()
                    title_input.input(title)
                    logger.info(f"✓ 标题已输入: {title[:30]}...")
                else:
                    # 备用选择器
                    title_input = self.page.ele('css:textarea[placeholder*="标题"]', timeout=3)
                    if title_input:
                        title_input.clear()
                        title_input.input(title)
                        logger.info(f"✓ 标题已输入(备用方法): {title[:30]}...")
            except Exception as e:
                logger.error(f"✗ 标题输入失败: {e}")
                return {'success': False, 'message': f'标题输入失败: {e}'}

            time.sleep(1)

            # 输入正文内容
            logger.info("正在输入正文...")
            try:
                # 尝试多种编辑器定位方式
                editor_selectors = [
                    'css:.public-DraftEditor-content',
                    'css:[contenteditable="true"]',
                    'css:.notranslate',
                    'css:[data-text="true"]'
                ]

                editor = None
                for selector in editor_selectors:
                    try:
                        editor = self.page.ele(selector, timeout=2)
                        if editor:
                            logger.info(f"✓ 找到编辑器: {selector}")
                            break
                    except:
                        continue

                if editor:
                    # 点击编辑器激活
                    editor.click()
                    time.sleep(0.5)

                    # 输入内容 - 一次性输入完整内容，避免被覆盖
                    logger.info(f"准备输入内容，长度: {len(content)} 字符")
                    editor.input(content, clear=True)
                    time.sleep(1)

                    # 验证内容是否输入成功
                    paragraphs = content.split('\n\n')
                    logger.info(f"✓ 正文已输入,共{len(paragraphs)}段")
                else:
                    logger.error("✗ 未找到编辑器元素")
                    return {'success': False, 'message': '未找到编辑器'}

            except Exception as e:
                logger.error(f"✗ 正文输入失败: {e}")
                return {'success': False, 'message': f'正文输入失败: {e}'}

            time.sleep(2)

            # 添加话题标签(如果提供)
            if topics:
                logger.info(f"正在添加话题: {topics}")
                try:
                    # 查找话题输入框
                    topic_input = self.page.ele('css:input[placeholder*="话题"]', timeout=3)
                    if topic_input:
                        for topic in topics:
                            topic_input.input(topic)
                            time.sleep(0.5)
                            # 按回车确认
                            topic_input.input('\n')
                            time.sleep(0.5)
                        logger.info(f"✓ 话题已添加: {topics}")
                except Exception as e:
                    logger.warning(f"话题添加失败(非关键): {e}")

            # 发布或保存草稿
            if draft:
                logger.info("正在保存草稿...")
                try:
                    save_draft_btn = self.page.ele('text:保存草稿', timeout=3)
                    if save_draft_btn:
                        save_draft_btn.click()
                        time.sleep(2)
                        logger.info("✓✓ 草稿保存成功")
                        return {'success': True, 'message': '草稿保存成功', 'type': 'draft'}
                except Exception as e:
                    logger.warning(f"保存草稿按钮未找到: {e}")
            else:
                logger.info("正在发布文章...")
                try:
                    # 查找发布按钮
                    publish_selectors = [
                        'text:发布文章',
                        'text:发布',
                        'css:button.PublishButton',
                        'css:button[type="submit"]'
                    ]

                    publish_btn = None
                    for selector in publish_selectors:
                        try:
                            publish_btn = self.page.ele(selector, timeout=2)
                            if publish_btn:
                                logger.info(f"✓ 找到发布按钮: {selector}")
                                break
                        except:
                            continue

                    if publish_btn:
                        logger.info("步骤3/5: 点击发布按钮...")
                        publish_btn.click()
                        logger.info("✓ 已点击发布按钮，等待页面响应...")
                        time.sleep(8)  # 延长等待时间从3秒到8秒

                        # 步骤4/5: 处理发布设置弹窗（重要！）
                        logger.info("步骤4/5: 检查发布设置弹窗...")

                        # 调试：保存当前页面截图和HTML(仅在DEBUG模式)
                        try:
                            import tempfile
                            debug_dir = '/tmp/zhihu_debug'
                            os.makedirs(debug_dir, exist_ok=True)

                            # 保存截图
                            screenshot_path = os.path.join(debug_dir, 'after_publish_click.png')
                            self.page.get_screenshot(screenshot_path)
                            logger.debug(f"✓ 截图已保存: {screenshot_path}")

                            # 保存HTML
                            html_path = os.path.join(debug_dir, 'after_publish_click.html')
                            with open(html_path, 'w', encoding='utf-8') as f:
                                f.write(self.page.html)
                            logger.debug(f"✓ HTML已保存: {html_path}")
                        except Exception as e:
                            logger.debug(f"保存调试信息失败: {e}")

                        # 知乎现在显示"发布设置"面板，需要点击面板底部的"发布"按钮
                        modal_found = False
                        modal_publish_selectors = [
                            # 新版知乎发布设置面板中的发布按钮
                            'css:button.Button--primary.Button--blue',  # 主要按钮样式
                            'css:.css-1ppjin3 button.Button--primary',  # 发布设置面板底部的主按钮
                            # 旧版选择器（向后兼容）
                            'text:发布文章',
                            'css:.Modal button.Button--primary',
                            'css:div[role="dialog"] button:has-text("发布")',
                            'css:.PublishPanel button.Button--primary',
                        ]

                        for selector in modal_publish_selectors:
                            try:
                                modal_btn = self.page.ele(selector, timeout=2)
                                if modal_btn:
                                    modal_text = modal_btn.text.strip()
                                    logger.info(f"✓ 找到可能的发布按钮: selector='{selector}', text='{modal_text}'")

                                    # 确保这是发布设置对话框中的按钮
                                    if '发布' in modal_text:
                                        logger.info(f"✓ 确认为发布按钮，准备点击")
                                        modal_btn.click()
                                        logger.info("✓ 已点击弹窗中的发布按钮")
                                        modal_found = True
                                        time.sleep(8)  # 延长等待时间
                                        break
                            except Exception as e:
                                logger.debug(f"选择器 '{selector}' 未找到元素: {e}")
                                continue

                        if not modal_found:
                            logger.warning("⚠ 未检测到发布设置弹窗，可能已直接发布或页面结构变化")

                        # 步骤5/5: 验证发布结果(带重试机制)
                        logger.info("步骤5/5: 验证发布结果...")

                        # 重试机制: 最多验证2次
                        max_retries = 2
                        publish_success = False
                        current_url = None
                        success_indicators = []

                        for retry_count in range(max_retries):
                            if retry_count > 0:
                                logger.info(f"第{retry_count + 1}次验证(重试 {retry_count})...")
                                time.sleep(6)  # 重试前额外等待6秒
                            else:
                                time.sleep(5)  # 首次验证等待5秒

                            current_url = self.page.url
                            logger.info(f"当前URL: {current_url}")

                            # 判断发布成功的标准
                            success_indicators = []

                            # 1. URL必须不包含 /edit（关键！）
                            if '/edit' not in current_url:
                                success_indicators.append("URL不包含/edit（已退出编辑模式）")
                            else:
                                logger.warning("⚠ URL仍然包含/edit，文章可能未真正发布")

                            # 2. URL应该包含文章ID
                            if '/p/' in current_url or '/zhuanlan/' in current_url:
                                success_indicators.append("URL包含文章路径")

                            # 3. URL应该不是write页面
                            if 'write' not in current_url:
                                success_indicators.append("URL已离开写作页面")

                            # 4. 检查页面是否有编辑按钮（发布后的文章页会有编辑按钮）
                            try:
                                # 如果能找到"编辑文章"按钮，说明在文章查看页面
                                edit_btn = self.page.ele('text:编辑文章', timeout=2)
                                if edit_btn:
                                    success_indicators.append("找到文章编辑按钮（说明在已发布文章页面）")
                            except:
                                pass

                            # 5. 检查是否有发布成功的提示
                            try:
                                page_html = self.page.html
                                if '发布成功' in page_html or '已发布' in page_html:
                                    success_indicators.append("页面显示发布成功")
                            except:
                                pass

                            # 综合判断
                            logger.info(f"成功指标数量: {len(success_indicators)}")
                            logger.info(f"成功指标: {success_indicators}")

                            # 关键判断:
                            # 1. URL不能包含/edit (编辑模式)
                            # 2. URL必须包含/p/ (已发布文章的标志)
                            # 3. URL不能是write页面
                            is_not_edit = '/edit' not in current_url
                            is_published_url = '/p/' in current_url
                            is_not_write = 'write' not in current_url

                            if is_not_edit and is_published_url and is_not_write:
                                logger.info(f"✓ 发布验证成功(第{retry_count + 1}次尝试)")
                                logger.info(f"  - URL不包含/edit: {is_not_edit}")
                                logger.info(f"  - URL包含/p/: {is_published_url}")
                                logger.info(f"  - URL不是write页面: {is_not_write}")
                                publish_success = True
                                break
                            else:
                                # 详细记录失败原因
                                fail_reasons = []
                                if not is_not_edit:
                                    fail_reasons.append("URL仍包含/edit")
                                if not is_published_url:
                                    fail_reasons.append("URL不包含/p/(非已发布文章)")
                                if not is_not_write:
                                    fail_reasons.append("URL仍在write页面")

                                if retry_count < max_retries - 1:
                                    logger.warning(f"⚠ 第{retry_count + 1}次验证失败: {', '.join(fail_reasons)}")
                                    logger.warning("将进行重试...")
                                else:
                                    logger.error(f"✗ 所有重试均失败,文章未真正发布: {', '.join(fail_reasons)}")

                        # 最终判断
                        if not publish_success:
                            # 更详细的错误消息
                            if '/edit' in current_url:
                                error_msg = "文章未真正发布，仍在编辑状态（URL包含/edit）"
                            elif '/p/' not in current_url:
                                error_msg = "文章未真正发布，URL不是已发布文章格式（应包含/p/）"
                            elif 'write' in current_url:
                                error_msg = "文章未真正发布，仍在写作页面"
                            else:
                                error_msg = "文章未真正发布，URL格式不符合预期"

                            logger.error(f"✗ {error_msg}")
                            logger.error(f"✗ 当前URL: {current_url}")
                            return {
                                'success': False,
                                'message': error_msg,
                                'url': current_url
                            }

                        # 发布成功
                        logger.info(f"✓✓✓ 文章已成功发布! URL: {current_url}")
                        return {
                            'success': True,
                            'message': '文章发布成功',
                            'type': 'published',
                            'url': current_url
                        }

                    else:
                        logger.error("✗ 未找到发布按钮")
                        return {'success': False, 'message': '未找到发布按钮'}

                except Exception as e:
                    logger.error(f"✗ 发布失败: {e}")
                    return {'success': False, 'message': f'发布失败: {e}'}

        except Exception as e:
            logger.error(f"✗ 创建文章异常: {e}", exc_info=True)
            return {'success': False, 'message': str(e)}

    def close(self):
        """关闭浏览器"""
        try:
            if self.page:
                logger.info("正在关闭浏览器...")
                self.page.quit()
                logger.info("✓ 浏览器已关闭")
        except Exception as e:
            logger.warning(f"关闭浏览器时出错: {e}")


# 便捷函数 - 增强版支持自动登录
def post_article_to_zhihu(username, title, content, password=None, topics=None, draft=False):
    """
    一键发布文章到知乎（增强版 - 支持自动登录）

    Args:
        username: 知乎账号(用于加载Cookie)
        title: 文章标题
        content: 文章内容
        password: 密码（可选，当Cookie不存在时使用）
        topics: 话题列表
        draft: 是否保存为草稿

    Returns:
        {'success': True/False, 'message': '...', 'url': '...'}
    """
    logger.info("[发布流程-发布器] ========== 知乎发布器开始 ==========")
    logger.info(f"[发布流程-发布器] 用户名: {username}")
    logger.info(f"[发布流程-发布器] 文章标题: {title[:50]}")
    logger.info(f"[发布流程-发布器] 文章长度: {len(content)} 字符")
    logger.info(f"[发布流程-发布器] 是否草稿: {draft}")
    logger.info(f"[发布流程-发布器] 是否提供密码: {'是' if password else '否'}")

    poster = ZhihuAutoPost()

    try:
        # 初始化浏览器
        logger.info("[发布流程-发布器] 步骤1: 初始化浏览器")
        if not poster.init_browser():
            logger.error("[发布流程-发布器] 浏览器初始化失败")
            return {'success': False, 'message': '浏览器初始化失败'}

        logger.info("[发布流程-发布器] ✓ 浏览器初始化成功")

        # 优先使用Cookie登录，失败则使用密码登录
        login_success = False

        # 步骤2.1: 尝试Cookie登录
        logger.info("=" * 60)
        logger.info("[发布流程-发布器] 步骤2: 尝试Cookie登录")
        logger.info("=" * 60)

        if poster.load_cookies(username):
            logger.info("[发布流程-发布器] ✓ Cookie登录成功")
            login_success = True
        else:
            # Cookie登录失败，尝试密码登录
            logger.warning("[发布流程-发布器] Cookie登录失败或不存在")

            if password:
                logger.info("=" * 60)
                logger.info("[发布流程-发布器] 步骤2.1: 使用账号密码登录（支持验证码自动识别）")
                logger.info("=" * 60)

                if poster.auto_login_with_password(username, password):
                    logger.info("[发布流程-发布器] ✓✓ 密码登录成功")
                    login_success = True
                else:
                    logger.error("[发布流程-发布器] 密码登录也失败")
                    return {
                        'success': False,
                        'message': '登录失败。Cookie无效且密码登录失败，请检查账号密码是否正确。'
                    }
            else:
                logger.error("[发布流程-发布器] Cookie无效且未配置密码")
                return {
                    'success': False,
                    'message': 'Cookie无效且未配置密码，无法登录。请在账号管理中配置知乎账号密码。'
                }

        # 登录成功，发布文章
        logger.info("=" * 60)
        logger.info("[发布流程-发布器] 步骤3: 开始发布文章到知乎")
        logger.info("=" * 60)

        result = poster.create_article(title, content, topics, draft)

        if result.get('success'):
            logger.info("[发布流程-发布器] ✓✓✓ 文章发布成功!")
            logger.info(f"[发布流程-发布器] 文章URL: {result.get('url')}")
        else:
            logger.error(f"[发布流程-发布器] ✗ 文章发布失败: {result.get('message')}")

        logger.info("[发布流程-发布器] ========== 知乎发布器结束 ==========")
        return result

    except Exception as e:
        logger.error(f"[发布流程-发布器] 发布过程异常: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'message': f'发布异常: {str(e)}'
        }
    finally:
        logger.debug("[发布流程-发布器] 关闭浏览器")
        poster.close()
