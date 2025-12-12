#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
终极版登录测试器
结合DrissionPage + undetected-chromedriver + 反检测技术
实现最强的验证码绕过能力
"""
import logging
import os
import json
import time
import random
from pathlib import Path

# 设置DISPLAY环境变量
if 'DISPLAY' not in os.environ:
    os.environ['DISPLAY'] = ':99'

# 尝试导入DrissionPage
try:
    from DrissionPage import ChromiumPage, ChromiumOptions
    HAS_DRISSION = True
except ImportError:
    HAS_DRISSION = False

# 尝试导入undetected-chromedriver
try:
    import undetected_chromedriver as uc
    HAS_UNDETECTED = True
except ImportError:
    HAS_UNDETECTED = False

# 标准Selenium作为备用
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logger = logging.getLogger(__name__)

class LoginTesterUltimate:
    """
    终极版登录测试器

    优先级策略:
    1. DrissionPage (最佳反检测，中文友好)
    2. undetected-chromedriver (次优，成熟稳定)
    3. Selenium + 反检测优化 (备用方案)
    """

    def __init__(self, headless=True, cookie_dir=None, mode='auto'):
        """
        初始化登录测试器

        :param headless: 是否使用无头模式
        :param cookie_dir: Cookie存储目录
        :param mode: 模式选择 ('auto', 'drission', 'undetected', 'selenium')
        """
        self.headless = headless
        self.mode = mode
        self.driver = None
        self.page = None  # DrissionPage对象

        # Cookie目录
        if cookie_dir is None:
            self.cookie_dir = Path(__file__).parent / 'cookies'
        else:
            self.cookie_dir = Path(cookie_dir)
        self.cookie_dir.mkdir(parents=True, exist_ok=True)

        # 确定使用的模式
        if mode == 'auto':
            if HAS_DRISSION:
                self.actual_mode = 'drission'
                logger.info("✓ Auto mode: Using DrissionPage (最佳)")
            elif HAS_UNDETECTED:
                self.actual_mode = 'undetected'
                logger.info("✓ Auto mode: Using undetected-chromedriver (次优)")
            else:
                self.actual_mode = 'selenium'
                logger.info("⚠ Auto mode: Using Selenium with anti-detection (备用)")
        else:
            self.actual_mode = mode

        logger.info(f"Mode: {self.actual_mode}, Headless: {headless}")

    # ==================== 初始化方法 ====================

    def init_driver(self):
        """根据模式初始化Driver"""
        try:
            if self.actual_mode == 'drission':
                return self._init_drission()
            elif self.actual_mode == 'undetected':
                return self._init_undetected()
            else:
                return self._init_selenium()
        except Exception as e:
            logger.error(f"Failed to init driver in {self.actual_mode} mode: {e}")
            # 尝试降级
            if self.actual_mode == 'drission':
                logger.info("Falling back to undetected-chromedriver...")
                self.actual_mode = 'undetected'
                return self._init_undetected()
            elif self.actual_mode == 'undetected':
                logger.info("Falling back to Selenium...")
                self.actual_mode = 'selenium'
                return self._init_selenium()
            return False

    def _init_drission(self):
        """初始化DrissionPage"""
        if not HAS_DRISSION:
            logger.error("DrissionPage not installed")
            return False

        try:
            logger.info("Initializing DrissionPage...")

            # 创建配置
            co = ChromiumOptions()

            # 基础配置
            if self.headless:
                co.headless(True)

            # Chrome路径
            import platform
            if platform.system() != 'Windows':
                co.set_browser_path('/usr/bin/google-chrome')

            # 无沙盒模式(服务器必需)
            co.set_argument('--no-sandbox')
            co.set_argument('--disable-dev-shm-usage')
            co.set_argument('--disable-gpu')

            # 窗口大小
            co.set_argument('--window-size=1920,1080')

            # 真实User-Agent
            co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36')

            # 创建页面对象（DrissionPage自带反检测）
            self.page = ChromiumPage(addr_or_opts=co)

            logger.info("✓ DrissionPage initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to init DrissionPage: {e}", exc_info=True)
            return False

    def _init_undetected(self):
        """初始化undetected-chromedriver"""
        if not HAS_UNDETECTED:
            logger.error("undetected-chromedriver not installed")
            return False

        try:
            logger.info("Initializing undetected-chromedriver...")

            import platform

            options = uc.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36')

            if self.headless:
                options.add_argument('--headless=new')

            if platform.system() != 'Windows':
                options.binary_location = '/usr/bin/google-chrome'

            # ChromeDriver路径
            driver_path = None
            if platform.system() != 'Windows':
                if os.path.exists('/home/u_topn/chromedriver'):
                    driver_path = '/home/u_topn/chromedriver'

            # 创建driver
            self.driver = uc.Chrome(
                options=options,
                driver_executable_path=driver_path,
                version_main=143,
                use_subprocess=False,
                headless=self.headless
            )

            self.driver.implicitly_wait(10)
            self._apply_stealth_scripts(self.driver)

            logger.info("✓ undetected-chromedriver initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to init undetected-chromedriver: {e}", exc_info=True)
            return False

    def _init_selenium(self):
        """初始化Selenium + 反检测"""
        try:
            logger.info("Initializing Selenium with anti-detection...")

            import platform

            options = Options()

            if self.headless:
                options.add_argument('--headless')

            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36')

            # 反检测配置
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)

            if platform.system() == 'Windows':
                options.binary_location = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
            else:
                options.binary_location = '/usr/bin/google-chrome'

            driver_path = None
            if platform.system() != 'Windows':
                if os.path.exists('/home/u_topn/chromedriver'):
                    driver_path = '/home/u_topn/chromedriver'

            if driver_path:
                self.driver = webdriver.Chrome(executable_path=driver_path, options=options)
            else:
                self.driver = webdriver.Chrome(options=options)

            self.driver.implicitly_wait(10)
            self._apply_stealth_scripts(self.driver)

            logger.info("✓ Selenium initialized with anti-detection")
            return True

        except Exception as e:
            logger.error(f"Failed to init Selenium: {e}", exc_info=True)
            return False

    def _apply_stealth_scripts(self, driver):
        """应用反检测脚本"""
        try:
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['zh-CN', 'zh', 'en-US', 'en']
                    });
                    window.chrome = { runtime: {} };
                    Object.defineProperty(navigator, 'permissions', {
                        get: () => ({
                            query: () => Promise.resolve({state: 'granted'})
                        })
                    });
                '''
            })
            logger.debug("✓ Stealth scripts applied")
        except Exception as e:
            logger.warning(f"Could not apply stealth scripts: {e}")

    # ==================== Cookie管理 ====================

    def _get_cookie_file(self, platform, username):
        """获取Cookie文件路径"""
        safe_username = username.replace('@', '_at_').replace('.', '_dot_')
        return self.cookie_dir / f"{platform}_{safe_username}.json"

    def save_cookies(self, platform, username):
        """保存Cookie"""
        cookie_file = self._get_cookie_file(platform, username)

        try:
            if self.actual_mode == 'drission' and self.page:
                # DrissionPage方式
                self.page.cookies.save(str(cookie_file))
                logger.info(f"✓ Cookies saved (DrissionPage): {cookie_file}")
                return True
            elif self.driver:
                # Selenium/undetected方式
                cookies = self.driver.get_cookies()
                with open(cookie_file, 'w', encoding='utf-8') as f:
                    json.dump(cookies, f, ensure_ascii=False, indent=2)
                logger.info(f"✓ Cookies saved (Selenium): {cookie_file}")
                return True
        except Exception as e:
            logger.error(f"Failed to save cookies: {e}")
            return False

    def load_cookies(self, platform, username):
        """加载Cookie"""
        cookie_file = self._get_cookie_file(platform, username)

        if not cookie_file.exists():
            logger.warning(f"Cookie file not found: {cookie_file}")
            return False

        try:
            if self.actual_mode == 'drission' and self.page:
                # DrissionPage方式
                platform_urls = {
                    '知乎': 'https://www.zhihu.com',
                    'CSDN': 'https://www.csdn.net'
                }
                if platform in platform_urls:
                    self.page.get(platform_urls[platform])
                    time.sleep(1)
                    self.page.cookies.load(str(cookie_file))
                    logger.info(f"✓ Cookies loaded (DrissionPage): {cookie_file}")
                    return True
            elif self.driver:
                # Selenium/undetected方式
                with open(cookie_file, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)

                platform_urls = {
                    '知乎': 'https://www.zhihu.com',
                    'CSDN': 'https://www.csdn.net'
                }
                if platform in platform_urls:
                    self.driver.get(platform_urls[platform])
                    time.sleep(1)

                for cookie in cookies:
                    try:
                        if 'expiry' in cookie:
                            cookie['expiry'] = int(cookie['expiry'])
                        if 'sameSite' in cookie and cookie['sameSite'] not in ['Strict', 'Lax', 'None']:
                            del cookie['sameSite']
                        self.driver.add_cookie(cookie)
                    except Exception as e:
                        logger.debug(f"Failed to add cookie: {e}")
                        continue

                logger.info(f"✓ Cookies loaded (Selenium): {cookie_file}")
                return True
        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")
            return False

    def check_cookie_exists(self, platform, username):
        """检查Cookie是否存在"""
        return self._get_cookie_file(platform, username).exists()

    # ==================== 人类行为模拟 ====================

    def human_like_delay(self, min_delay=0.5, max_delay=1.5):
        """随机延迟"""
        time.sleep(random.uniform(min_delay, max_delay))

    def human_like_input(self, element, text):
        """模拟真人输入"""
        if self.actual_mode == 'drission':
            # DrissionPage自动处理
            element.input(text)
        else:
            # Selenium需要模拟
            for char in text:
                element.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))

    # ==================== 知乎登录 ====================

    def test_zhihu_login(self, username, password, use_cookie=True, max_retries=2):
        """
        智能多策略登录

        策略:
        1. Cookie登录 (最快，100%成功率)
        2. 反检测密码登录 (DrissionPage/undetected)
        3. 自动重试 + 人工介入
        """
        for attempt in range(max_retries):
            try:
                logger.info(f"=== 登录尝试 {attempt + 1}/{max_retries} (模式: {self.actual_mode}) ===")

                # 初始化driver
                if not self.driver and not self.page:
                    if not self.init_driver():
                        return {'success': False, 'message': 'Driver初始化失败'}

                # 策略1: Cookie登录
                if use_cookie and self.check_cookie_exists('知乎', username):
                    logger.info("策略1: 尝试Cookie登录...")
                    result = self._cookie_login_zhihu(username)
                    if result['success']:
                        return result
                    logger.warning("Cookie失效，使用密码登录")

                # 策略2: 密码登录
                logger.info(f"策略2: 密码登录 (模式: {self.actual_mode})...")
                result = self._password_login_zhihu(username, password)

                if result['success']:
                    if use_cookie:
                        self.save_cookies('知乎', username)
                    return result

                # 检查验证码
                if 'captcha' in result.get('message', '').lower():
                    logger.warning(f"[尝试{attempt + 1}] 遇到验证码")

                    if attempt < max_retries - 1:
                        logger.info("重试...")
                        self.quit_driver()
                        time.sleep(3)
                        continue
                    else:
                        logger.info("等待人工处理验证码...")
                        return self._wait_for_manual_captcha(username, 60)

            except Exception as e:
                logger.error(f"[尝试{attempt + 1}] 错误: {e}", exc_info=True)
                if attempt < max_retries - 1:
                    self.quit_driver()
                    time.sleep(3)
                    continue

        return {'success': False, 'message': '登录失败'}

    def _cookie_login_zhihu(self, username):
        """使用Cookie登录知乎"""
        try:
            if not self.load_cookies('知乎', username):
                return {'success': False, 'message': 'Cookie加载失败'}

            if self.actual_mode == 'drission':
                self.page.refresh()
                time.sleep(2)

                if 'signin' not in self.page.url:
                    logger.info("✓ Cookie登录成功 (DrissionPage)")
                    return {
                        'success': True,
                        'message': 'Cookie登录成功',
                        'method': 'cookie_drission',
                        'current_url': self.page.url
                    }
            else:
                self.driver.get('https://www.zhihu.com')
                time.sleep(2)

                if 'signin' not in self.driver.current_url:
                    logger.info(f"✓ Cookie登录成功 ({self.actual_mode})")
                    return {
                        'success': True,
                        'message': 'Cookie登录成功',
                        'method': f'cookie_{self.actual_mode}',
                        'current_url': self.driver.current_url
                    }

            return {'success': False, 'message': 'Cookie已过期'}

        except Exception as e:
            logger.error(f"Cookie登录错误: {e}")
            return {'success': False, 'message': f'Cookie登录异常: {str(e)}'}

    def _password_login_zhihu(self, username, password):
        """密码登录知乎"""
        try:
            if self.actual_mode == 'drission':
                return self._password_login_drission(username, password)
            else:
                return self._password_login_selenium(username, password)
        except Exception as e:
            logger.error(f"密码登录错误: {e}", exc_info=True)
            return {'success': False, 'message': f'密码登录异常: {str(e)}'}

    def _password_login_drission(self, username, password):
        """DrissionPage密码登录"""
        logger.info("使用DrissionPage登录...")

        # 访问登录页
        self.page.get('https://www.zhihu.com/signin')
        time.sleep(2)

        # 切换到密码登录
        password_btn = self.page.ele('text:密码登录', timeout=5)
        if password_btn:
            password_btn.click()
            time.sleep(1)
            logger.info("✓ 切换到密码登录模式")

        # 输入账号密码
        username_input = self.page.ele('@name=username')
        if username_input:
            username_input.input(username)
            logger.info("✓ 用户名输入完成")

        self.human_like_delay(0.5, 1.0)

        password_input = self.page.ele('@name=password')
        if password_input:
            password_input.input(password)
            logger.info("✓ 密码输入完成")

        self.human_like_delay(0.5, 1.0)

        # 点击登录
        login_btn = self.page.ele('@@type=submit')
        if login_btn:
            login_btn.click()
            logger.info("✓ 登录按钮已点击")

        time.sleep(3)

        # 检查结果
        if 'signin' not in self.page.url:
            logger.info("✓ 密码登录成功 (DrissionPage)")
            return {
                'success': True,
                'message': '知乎登录成功',
                'method': 'password_drission',
                'current_url': self.page.url
            }

        # 检查验证码
        if '验证' in self.page.html or 'captcha' in self.page.html.lower():
            return {
                'success': False,
                'message': '需要验证码',
                'needs_captcha': True
            }

        return {
            'success': False,
            'message': '登录失败，请检查账号密码'
        }

    def _password_login_selenium(self, username, password):
        """Selenium密码登录"""
        logger.info(f"使用{self.actual_mode}登录...")

        self.driver.get('https://www.zhihu.com/signin')
        time.sleep(2)

        # 切换到密码登录
        try:
            password_btn = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and text()='密码登录']"))
            )
            password_btn.click()
            time.sleep(1)
            logger.info("✓ 切换到密码登录模式")
        except:
            logger.warning("未找到密码登录按钮，可能已经在密码登录模式")

        # 输入账号
        username_input = self.driver.find_element(By.NAME, "username")
        self.human_like_input(username_input, username)
        logger.info("✓ 用户名输入完成")

        self.human_like_delay(0.5, 1.0)

        # 输入密码
        password_input = self.driver.find_element(By.NAME, "password")
        self.human_like_input(password_input, password)
        logger.info("✓ 密码输入完成")

        self.human_like_delay(0.5, 1.0)

        # 点击登录
        login_btn = self.driver.find_element(By.XPATH, "//button[@type='submit' and contains(@class, 'SignFlow-submitButton')]")
        login_btn.click()
        logger.info("✓ 登录按钮已点击")

        time.sleep(3)

        # 检查结果
        if 'signin' not in self.driver.current_url:
            logger.info(f"✓ 密码登录成功 ({self.actual_mode})")
            return {
                'success': True,
                'message': '知乎登录成功',
                'method': f'password_{self.actual_mode}',
                'current_url': self.driver.current_url
            }

        # 检查验证码
        if '验证' in self.driver.page_source or 'captcha' in self.driver.page_source.lower():
            return {
                'success': False,
                'message': '需要验证码',
                'needs_captcha': True
            }

        return {
            'success': False,
            'message': '登录失败，请检查账号密码'
        }

    def _wait_for_manual_captcha(self, username, timeout=60):
        """等待人工处理验证码"""
        logger.info(f"⏳ 等待人工处理验证码 (超时: {timeout}秒)...")

        for i in range(timeout):
            time.sleep(1)

            try:
                if self.actual_mode == 'drission':
                    if 'signin' not in self.page.url:
                        logger.info("✓ 人工验证码处理成功!")
                        self.save_cookies('知乎', username)
                        return {
                            'success': True,
                            'message': '登录成功（人工验证码）',
                            'method': 'manual_captcha'
                        }
                else:
                    if 'signin' not in self.driver.current_url:
                        logger.info("✓ 人工验证码处理成功!")
                        self.save_cookies('知乎', username)
                        return {
                            'success': True,
                            'message': '登录成功（人工验证码）',
                            'method': 'manual_captcha'
                        }
            except:
                pass

            if i % 10 == 0 and i > 0:
                logger.info(f"仍在等待... ({i}/{timeout}秒)")

        return {'success': False, 'message': '验证码处理超时'}

    def quit_driver(self):
        """关闭Driver"""
        try:
            if self.page:
                self.page.quit()
                self.page = None
            if self.driver:
                self.driver.quit()
                self.driver = None
            logger.debug("Driver已关闭")
        except Exception as e:
            logger.warning(f"关闭Driver错误: {e}")

    def __del__(self):
        """析构函数"""
        self.quit_driver()


# 测试代码
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # 创建终极版测试器
    tester = LoginTesterUltimate(headless=False, mode='auto')

    # 测试登录
    result = tester.test_zhihu_login(
        username="13751156900",
        password="your_password",
        use_cookie=True
    )

    print("\n" + "="*80)
    print("登录结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("="*80)

    tester.quit_driver()
