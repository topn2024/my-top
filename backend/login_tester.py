#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
账号登录测试模块
使用Selenium实现真实的网站登录测试
支持Cookie持久化登录
"""
import logging
import os
import json
from pathlib import Path

# 在模块级别设置DISPLAY环境变量，确保在导入webdriver之前设置
if 'DISPLAY' not in os.environ:
    os.environ['DISPLAY'] = ':99'

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

# Try to import webdriver_manager
try:
    from webdriver_manager.chrome import ChromeDriverManager
    HAS_WEBDRIVER_MANAGER = True
except ImportError:
    HAS_WEBDRIVER_MANAGER = False

logger = logging.getLogger(__name__)

class LoginTester:
    """网站登录测试器"""

    def __init__(self, headless=True, cookie_dir=None):
        """
        初始化登录测试器
        :param headless: 是否使用无头模式（服务器环境需要）
        :param cookie_dir: Cookie存储目录，默认为当前目录下的cookies文件夹
        """
        self.headless = headless
        self.driver = None

        # 设置Cookie存储目录
        if cookie_dir is None:
            self.cookie_dir = Path(__file__).parent / 'cookies'
        else:
            self.cookie_dir = Path(cookie_dir)

        # 确保Cookie目录存在
        self.cookie_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Cookie directory: {self.cookie_dir}")

    def init_driver(self):
        """初始化WebDriver"""
        try:
            # 设置DISPLAY环境变量（headless模式仍需要）
            import os
            logger.info(f"Initializing WebDriver (headless={self.headless})")

            current_display = os.environ.get('DISPLAY', 'Not set')
            logger.debug(f"Current DISPLAY environment: {current_display}")

            if 'DISPLAY' not in os.environ:
                os.environ['DISPLAY'] = ':99'
                logger.info("Set DISPLAY=:99")

            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument('--headless')
                logger.debug("Enabled headless mode")

            # 关键选项 - 解决Chrome在服务器上的问题
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-software-rasterizer')
            chrome_options.add_argument('--disable-extensions')

            # 窗口选项
            chrome_options.add_argument('--window-size=1920,1080')

            # User agent
            chrome_options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36')

            # 其他兼容性选项
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')

            # 日志和稳定性
            chrome_options.add_argument('--log-level=3')
            chrome_options.add_argument('--silent')

            # 显式指定Chrome binary位置
            # 根据操作系统选择Chrome路径
            import platform
            system = platform.system()
            logger.debug(f"Detected platform: {system}")

            if system == 'Windows':
                # Windows Chrome路径
                chrome_options.binary_location = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
            else:
                # Linux Chrome路径
                chrome_options.binary_location = '/usr/bin/google-chrome'

            logger.info(f"Chrome binary location: {chrome_options.binary_location}")

            # 检查Chrome是否存在
            if not os.path.exists(chrome_options.binary_location):
                logger.error(f"Chrome binary not found at: {chrome_options.binary_location}")
                return False

            # 方式1: 使用webdriver_manager自动下载匹配的ChromeDriver
            if HAS_WEBDRIVER_MANAGER:
                try:
                    logger.info("Using webdriver_manager to get ChromeDriver")
                    driver_path = ChromeDriverManager().install()
                    logger.debug(f"ChromeDriver path from webdriver_manager: {driver_path}")
                    self.driver = webdriver.Chrome(executable_path=driver_path, options=chrome_options)
                    self.driver.implicitly_wait(10)
                    logger.info(f"✓ WebDriver initialized successfully with webdriver_manager: {driver_path}")
                    return True
                except Exception as e:
                    logger.warning(f"webdriver_manager failed: {type(e).__name__}: {str(e)}")
                    logger.debug("Falling back to manual ChromeDriver paths", exc_info=True)

            # 方式2: 尝试多个可能的ChromeDriver位置
            if system == 'Windows':
                # Windows可能的ChromeDriver位置
                chromedriver_paths = [
                    'chromedriver.exe',  # 当前目录
                    r'C:\chromedriver\chromedriver.exe',
                ]
            else:
                # Linux可能的ChromeDriver位置
                chromedriver_paths = [
                    '/home/u_topn/chromedriver',
                    '/usr/local/bin/chromedriver',
                    '/usr/bin/chromedriver',
                ]

            logger.info(f"Trying {len(chromedriver_paths)} possible ChromeDriver locations")
            for path in chromedriver_paths:
                logger.debug(f"Checking path: {path}")
                if os.path.exists(path):
                    try:
                        logger.info(f"Found ChromeDriver at: {path}")
                        logger.debug(f"Attempting to initialize WebDriver with: {path}")
                        self.driver = webdriver.Chrome(executable_path=path, options=chrome_options)
                        self.driver.implicitly_wait(10)
                        logger.info(f"✓ WebDriver initialized successfully with: {path}")
                        return True
                    except Exception as e:
                        logger.error(f"✗ Failed with {path}: {type(e).__name__}: {str(e)}")
                        logger.debug(f"Full error for {path}:", exc_info=True)
                        continue
                else:
                    logger.debug(f"ChromeDriver not found at: {path}")

            # 方式3: 尝试使用系统PATH
            try:
                logger.info("Trying ChromeDriver from system PATH")
                self.driver = webdriver.Chrome(options=chrome_options)
                self.driver.implicitly_wait(10)
                logger.info("✓ WebDriver initialized successfully from system PATH")
                return True
            except Exception as e:
                logger.error(f"✗ Failed to initialize from system PATH: {type(e).__name__}: {str(e)}")
                logger.debug("System PATH initialization error:", exc_info=True)

            logger.error("All ChromeDriver initialization methods failed")
            return False

        except Exception as e:
            logger.error(f"Critical error in init_driver: {type(e).__name__}: {str(e)}", exc_info=True)
            return False

    def close_driver(self):
        """关闭WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None

    def _get_cookie_file(self, platform, username):
        """获取Cookie文件路径"""
        safe_username = username.replace('@', '_at_').replace('.', '_dot_')
        return self.cookie_dir / f"{platform}_{safe_username}.json"

    def save_cookies(self, platform, username):
        """保存当前会话的Cookie"""
        if not self.driver:
            logger.error("No active driver session to save cookies from")
            return False

        try:
            cookies = self.driver.get_cookies()
            cookie_file = self._get_cookie_file(platform, username)

            with open(cookie_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)

            logger.info(f"Cookies saved to {cookie_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save cookies: {e}")
            return False

    def load_cookies(self, platform, username):
        """加载Cookie到当前会话"""
        if not self.driver:
            logger.error("No active driver session to load cookies into")
            return False

        cookie_file = self._get_cookie_file(platform, username)
        if not cookie_file.exists():
            logger.warning(f"Cookie file not found: {cookie_file}")
            return False

        try:
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)

            # 先访问目标网站
            platform_urls = {
                '知乎': 'https://www.zhihu.com',
                'CSDN': 'https://www.csdn.net'
            }
            if platform in platform_urls:
                self.driver.get(platform_urls[platform])
                time.sleep(1)

            # 加载所有Cookie
            for cookie in cookies:
                try:
                    # 移除可能导致问题的字段
                    if 'expiry' in cookie:
                        cookie['expiry'] = int(cookie['expiry'])
                    if 'sameSite' in cookie and cookie['sameSite'] not in ['Strict', 'Lax', 'None']:
                        del cookie['sameSite']

                    self.driver.add_cookie(cookie)
                except Exception as e:
                    logger.debug(f"Failed to add cookie {cookie.get('name', 'unknown')}: {e}")
                    continue

            logger.info(f"Cookies loaded from {cookie_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")
            return False

    def check_cookie_exists(self, platform, username):
        """检查是否存在Cookie文件"""
        cookie_file = self._get_cookie_file(platform, username)
        return cookie_file.exists()

    def delete_cookies(self, platform, username):
        """删除Cookie文件"""
        cookie_file = self._get_cookie_file(platform, username)
        if cookie_file.exists():
            try:
                cookie_file.unlink()
                logger.info(f"Cookie file deleted: {cookie_file}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete cookie file: {e}")
                return False
        return False

    def test_zhihu_login(self, username, password, use_cookie=True):
        """测试知乎登录 - 支持Cookie登录和密码登录

        :param username: 用户名
        :param password: 密码
        :param use_cookie: 是否优先尝试使用Cookie登录
        """
        try:
            logger.info(f"Testing Zhihu login for user: {username}")

            # 如果启用Cookie登录且存在Cookie文件，尝试Cookie登录
            if use_cookie and self.check_cookie_exists('知乎', username):
                logger.info("Found existing cookies, trying cookie login...")

                # 加载Cookie
                if self.load_cookies('知乎', username):
                    # 刷新页面使Cookie生效
                    self.driver.get('https://www.zhihu.com')
                    time.sleep(2)

                    # 检查是否登录成功
                    current_url = self.driver.current_url
                    if 'signin' not in current_url:
                        logger.info("Cookie login successful!")

                        # 验证登录状态
                        success_indicators = [
                            (By.CLASS_NAME, "AppHeader-profile"),
                            (By.XPATH, "//div[contains(@class, 'AppHeader-profile')]"),
                        ]

                        for by, selector in success_indicators:
                            try:
                                WebDriverWait(self.driver, 3).until(
                                    EC.presence_of_element_located((by, selector))
                                )
                                logger.info("✓ Login verified - user profile found")
                                return {
                                    'success': True,
                                    'message': '使用Cookie登录成功！',
                                    'login_method': 'cookie',
                                    'current_url': current_url
                                }
                            except:
                                continue

                    logger.warning("Cookie login failed or expired, falling back to password login")
                else:
                    logger.warning("Failed to load cookies, using password login")

            # Cookie登录失败或未启用，使用密码登录
            logger.info("Using password login method...")

            # 访问知乎登录页
            logger.info("Opening Zhihu login page...")
            self.driver.get('https://www.zhihu.com/signin')
            time.sleep(3)
            logger.info(f"Current URL: {self.driver.current_url}")

            # 切换到密码登录模式 - 使用经过实际页面分析验证的选择器
            logger.info("Attempting to switch to password login mode...")
            logger.info("默认页面显示短信登录,需要切换到密码登录")
            password_login_switched = False

            # 等待页面加载完成
            time.sleep(2)

            # 使用经过实际页面分析验证的精确选择器
            try:
                # 基于2025-12-05的页面分析，使用验证过的选择器
                # 分析结果: <div role='button' class='SignFlow-tab' text='密码登录'>
                selectors = [
                    "//div[@role='button' and text()='密码登录']",  # 最精确 - 页面分析验证✓
                    "//div[text()='密码登录']",  # 备用 - 页面分析验证✓
                    "//div[@class='SignFlow-tab' and text()='密码登录']",  # 备用2 - 页面分析验证✓
                ]

                logger.info(f"Using {len(selectors)} verified selectors for password login button")

                for i, selector in enumerate(selectors, 1):
                    try:
                        logger.info(f"Attempt {i}/{len(selectors)}: {selector}")
                        password_tab = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        logger.info(f"✓ Found password login button: '{password_tab.text}'")

                        # 滚动到元素可见位置
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", password_tab)
                        time.sleep(0.3)

                        # 点击切换按钮
                        password_tab.click()
                        logger.info("✓ Clicked password login button")

                        # 等待并验证切换成功 - 密码输入框应该出现
                        try:
                            WebDriverWait(self.driver, 3).until(
                                EC.presence_of_element_located((By.NAME, "password"))
                            )
                            password_login_switched = True
                            logger.info("✓✓✓ Successfully switched to PASSWORD LOGIN mode ✓✓✓")
                            logger.info("✓ Verified: password input field is now visible")
                            break
                        except:
                            logger.warning("Clicked button but password field not found, trying next selector")
                            continue

                    except Exception as e:
                        logger.debug(f"Selector {i} failed: {type(e).__name__}")
                        continue

                if not password_login_switched:
                    logger.warning("Could not switch to password login mode")
                    logger.warning("Will try to proceed, but login may fail")

            except Exception as e:
                logger.error(f"Error while switching to password login: {e}", exc_info=True)

            # 输入用户名 - 使用页面分析验证的选择器
            # 分析结果: type='text' name='username' placeholder='手机号或邮箱'
            logger.info("Entering username...")
            username_input = None
            username_selectors = [
                (By.NAME, "username"),  # 最稳定 - 页面分析验证✓
                (By.XPATH, "//input[@name='username' and @type='text']"),  # 精确 - 页面分析验证✓
            ]

            for by, selector in username_selectors:
                try:
                    username_input = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((by, selector))
                    )
                    logger.info(f"✓ Found username field: {by}={selector}")
                    break
                except:
                    continue

            if not username_input:
                logger.error("Could not find username input field")
                return {
                    'success': False,
                    'message': '无法找到用户名输入框，页面结构可能已变化'
                }

            username_input.clear()
            username_input.send_keys(username)
            logger.info(f"✓ Username entered: {username}")
            time.sleep(0.5)

            # 输入密码 - 使用页面分析验证的选择器
            # 分析结果: type='password' name='password' placeholder='密码'
            logger.info("Entering password...")
            password_input = None
            password_selectors = [
                (By.NAME, "password"),  # 最稳定 - 页面分析验证✓
                (By.XPATH, "//input[@type='password']"),  # 备用 - 页面分析验证✓
            ]

            for by, selector in password_selectors:
                try:
                    password_input = self.driver.find_element(by, selector)
                    logger.info(f"✓ Found password field: {by}={selector}")
                    break
                except:
                    continue

            if not password_input:
                logger.error("Could not find password input field")
                return {
                    'success': False,
                    'message': '无法找到密码输入框，页面结构可能已变化'
                }

            password_input.clear()
            password_input.send_keys(password)
            logger.info("✓ Password entered")
            time.sleep(0.5)

            # 点击登录按钮 - 使用页面分析验证的选择器
            # 分析结果: type='submit' text='登录' class='Button SignFlow-submitButton ... Button--primary'
            logger.info("Clicking login button...")
            login_button = None
            login_button_selectors = [
                (By.XPATH, "//button[@type='submit' and contains(@class, 'SignFlow-submitButton')]"),  # 最精确 - 页面分析验证✓
                (By.XPATH, "//button[@type='submit' and text()='登录']"),  # 备用 - 页面分析验证✓
                (By.CSS_SELECTOR, "button.SignFlow-submitButton"),  # 备用2
            ]

            for by, selector in login_button_selectors:
                try:
                    login_button = self.driver.find_element(by, selector)
                    logger.info(f"✓ Found login button: {by}={selector}")
                    break
                except:
                    continue

            if not login_button:
                logger.error("Could not find login button")
                return {
                    'success': False,
                    'message': '无法找到登录按钮，页面结构可能已变化'
                }

            login_button.click()
            logger.info("✓ Login button clicked")

            # 等待登录完成
            logger.info("Waiting for login to complete...")
            time.sleep(4)

            current_url = self.driver.current_url
            page_content = self.driver.page_source
            logger.info(f"After login URL: {current_url}")

            # 检查登录是否成功
            if 'signin' not in current_url:
                logger.info("URL changed from signin page, checking for success indicators...")
                # 检查是否能找到用户信息元素
                success_indicators = [
                    (By.CLASS_NAME, "AppHeader-profile"),
                    (By.CSS_SELECTOR, ".AppHeader-profile"),
                    (By.XPATH, "//div[contains(@class, 'AppHeader-profile')]"),
                    (By.XPATH, "//*[contains(@class, 'Avatar')]")
                ]

                for by, selector in success_indicators:
                    try:
                        WebDriverWait(self.driver, 3).until(
                            EC.presence_of_element_located((by, selector))
                        )
                        logger.info(f"✓ Zhihu login successful - found indicator: {selector}")

                        # 登录成功，保存Cookie以便下次使用
                        if use_cookie:
                            self.save_cookies('知乎', username)
                            logger.info("✓ Cookies saved for future use")

                        return {
                            'success': True,
                            'message': '知乎登录成功！已进入主页',
                            'login_method': 'password',
                            'current_url': current_url
                        }
                    except:
                        continue

            # 检查是否需要验证码
            if '验证' in page_content or 'captcha' in current_url.lower() or 'verify' in current_url.lower():
                logger.warning("Login requires captcha verification")
                return {
                    'success': False,
                    'message': '登录需要验证码，请在网页端完成验证后重试'
                }

            # 检查是否有错误提示
            error_messages = ['账号或密码错误', '用户名或密码错误', '密码错误', '账号不存在']
            for error_msg in error_messages:
                if error_msg in page_content:
                    logger.warning(f"Login failed: {error_msg}")
                    return {
                        'success': False,
                        'message': f'登录失败: {error_msg}'
                    }

            logger.warning("Login status unknown")
            return {
                'success': False,
                'message': '登录状态未知，请检查账号密码或查看详细日志'
            }

        except TimeoutException:
            return {
                'success': False,
                'message': '登录超时，页面加载失败'
            }
        except Exception as e:
            logger.error(f"Zhihu login test failed: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'登录测试异常: {str(e)}'
            }

    def test_csdn_login(self, username, password):
        """测试CSDN登录 - 使用密码登录方式"""
        try:
            logger.info(f"Testing CSDN login for user: {username}")

            # 访问CSDN登录页
            logger.info("Opening CSDN login page...")
            self.driver.get('https://passport.csdn.net/login')
            time.sleep(3)
            logger.info(f"Current URL: {self.driver.current_url}")

            # 切换到密码登录 - 这是关键步骤
            logger.info("Attempting to switch to password login mode...")
            logger.info("默认页面可能显示验证码或短信登录,需要切换到密码登录")
            password_login_switched = False

            # 等待页面加载完成
            time.sleep(2)

            # 尝试查找并点击"密码登录"标签/按钮
            try:
                # 扩展选择器列表
                password_tab_selectors = [
                    # XPATH选择器
                    (By.XPATH, "//span[contains(text(), '密码登录')]"),
                    (By.XPATH, "//div[contains(text(), '密码登录')]"),
                    (By.XPATH, "//button[contains(text(), '密码登录')]"),
                    (By.XPATH, "//a[contains(text(), '密码登录')]"),
                    (By.XPATH, "//*[contains(text(), '密码登录')]"),
                    (By.XPATH, "//*[text()='密码登录']"),

                    # Class相关
                    (By.XPATH, "//div[contains(@class, 'login-box-tabs-items')]//span[contains(text(), '密码')]"),
                    (By.XPATH, "//div[contains(@class, 'tab')]//span[contains(text(), '密码')]"),

                    # CSS选择器
                    (By.CSS_SELECTOR, "span[contains='密码']"),
                    (By.CSS_SELECTOR, ".tab-item:contains('密码')"),

                    # 其他可能的结构
                    (By.XPATH, "//li[contains(text(), '密码登录')]"),
                    (By.XPATH, "//div[@role='tab' and contains(text(), '密码')]")
                ]

                logger.info(f"Trying {len(password_tab_selectors)} different selectors to find password login tab...")

                for i, (by, selector) in enumerate(password_tab_selectors, 1):
                    try:
                        logger.info(f"Attempt {i}/{len(password_tab_selectors)}: {by}={selector[:40]}...")
                        password_tab = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((by, selector))
                        )
                        logger.info(f"✓ Found password login tab with selector #{i}")

                        # 点击前先滚动到元素可见位置
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", password_tab)
                        time.sleep(0.5)

                        password_tab.click()
                        logger.info("✓ Clicked password login tab")
                        time.sleep(2)  # 等待切换完成

                        password_login_switched = True
                        logger.info("✓✓✓ Successfully switched to PASSWORD LOGIN mode ✓✓✓")
                        break
                    except Exception as e:
                        logger.debug(f"Selector {i} failed: {type(e).__name__}")
                        continue

                if not password_login_switched:
                    logger.warning("⚠ Could not find password login tab")
                    logger.warning("⚠ Assuming page is already on password login mode")
                    logger.warning("⚠ If login fails, the page might be showing captcha/SMS login by default")

            except Exception as e:
                logger.error(f"Error while switching to password login: {e}", exc_info=True)

            # 输入用户名 - 尝试多种选择器
            logger.info("Entering username...")
            username_input = None
            username_selectors = [
                (By.ID, "username"),
                (By.CSS_SELECTOR, "input#username"),
                (By.CSS_SELECTOR, "input[placeholder*='用户名']"),
                (By.CSS_SELECTOR, "input[placeholder*='手机号']"),
                (By.CSS_SELECTOR, "input[placeholder*='邮箱']"),
                (By.XPATH, "//input[@type='text']")
            ]

            for by, selector in username_selectors:
                try:
                    username_input = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((by, selector))
                    )
                    logger.info(f"✓ Found username field with: {by}={selector}")
                    break
                except:
                    continue

            if not username_input:
                logger.error("Could not find username input field")
                return {
                    'success': False,
                    'message': '无法找到用户名输入框，页面结构可能已变化'
                }

            username_input.clear()
            username_input.send_keys(username)
            logger.info("✓ Username entered")
            time.sleep(0.5)

            # 输入密码 - 尝试多种选择器
            logger.info("Entering password...")
            password_input = None
            password_selectors = [
                (By.ID, "password"),
                (By.CSS_SELECTOR, "input#password"),
                (By.CSS_SELECTOR, "input[type='password']"),
                (By.XPATH, "//input[@type='password']")
            ]

            for by, selector in password_selectors:
                try:
                    password_input = self.driver.find_element(by, selector)
                    logger.info(f"✓ Found password field with: {by}={selector}")
                    break
                except:
                    continue

            if not password_input:
                logger.error("Could not find password input field")
                return {
                    'success': False,
                    'message': '无法找到密码输入框，页面结构可能已变化'
                }

            password_input.clear()
            password_input.send_keys(password)
            logger.info("✓ Password entered")
            time.sleep(0.5)

            # 点击登录按钮 - 尝试多种选择器
            logger.info("Clicking login button...")
            login_button = None
            login_button_selectors = [
                (By.CLASS_NAME, "btn-login"),
                (By.CSS_SELECTOR, "button.btn-login"),
                (By.XPATH, "//button[contains(@class, 'btn-login')]"),
                (By.XPATH, "//button[contains(text(), '登录')]"),
                (By.CSS_SELECTOR, "button[type='submit']")
            ]

            for by, selector in login_button_selectors:
                try:
                    login_button = self.driver.find_element(by, selector)
                    logger.info(f"✓ Found login button with: {by}={selector}")
                    break
                except:
                    continue

            if not login_button:
                logger.error("Could not find login button")
                return {
                    'success': False,
                    'message': '无法找到登录按钮，页面结构可能已变化'
                }

            login_button.click()
            logger.info("✓ Login button clicked")

            # 等待登录完成
            logger.info("Waiting for login to complete...")
            time.sleep(4)

            current_url = self.driver.current_url
            logger.info(f"After login URL: {current_url}")

            # 检查是否登录成功
            if 'passport.csdn.net' not in current_url:
                logger.info("URL changed from passport page, checking for success indicators...")
                # 尝试多个成功指标
                success_indicators = [
                    (By.CLASS_NAME, "toolbar-container-middle"),
                    (By.CSS_SELECTOR, ".toolbar-container-middle"),
                    (By.XPATH, "//div[contains(@class, 'toolbar-container')]"),
                    (By.XPATH, "//*[contains(@class, 'user-profile')]"),
                    (By.XPATH, "//*[contains(@class, 'avatar')]")
                ]

                for by, selector in success_indicators:
                    try:
                        WebDriverWait(self.driver, 3).until(
                            EC.presence_of_element_located((by, selector))
                        )
                        logger.info(f"✓ CSDN login successful - found indicator: {selector}")
                        return {
                            'success': True,
                            'message': 'CSDN登录成功！',
                            'current_url': current_url
                        }
                    except:
                        continue

            # 检查是否需要验证码
            page_content = self.driver.page_source
            if '验证' in page_content or 'captcha' in current_url.lower():
                logger.warning("Login requires captcha verification")
                return {
                    'success': False,
                    'message': '需要验证码验证，请在网页端完成验证后重试'
                }

            # 检查是否有错误提示
            error_messages = ['账号或密码错误', '用户名或密码错误', '密码错误', '账号不存在', '登录失败']
            for error_msg in error_messages:
                if error_msg in page_content:
                    logger.warning(f"Login failed: {error_msg}")
                    return {
                        'success': False,
                        'message': f'登录失败: {error_msg}'
                    }

            logger.warning("Login status unknown")
            return {
                'success': False,
                'message': '登录失败，请检查账号密码或查看详细日志'
            }

        except Exception as e:
            logger.error(f"CSDN login test failed: {e}", exc_info=True)
            return {'success': False, 'message': f'登录测试异常: {str(e)}'}

    def test_login(self, platform, username, password):
        """
        测试账号登录
        :param platform: 平台名称
        :param username: 用户名
        :param password: 密码
        :return: dict with 'success', 'message', 'current_url' (optional)
        """
        if not self.init_driver():
            return {
                'success': False,
                'message': 'WebDriver初始化失败，请检查Chrome和ChromeDriver是否已安装'
            }

        try:
            # 根据平台调用不同的登录方法
            if platform == '知乎':
                result = self.test_zhihu_login(username, password)
            elif platform == 'CSDN':
                result = self.test_csdn_login(username, password)
            else:
                # 对于其他平台，返回提示信息
                result = {
                    'success': False,
                    'message': f'暂不支持 {platform} 的自动登录测试，该功能正在开发中'
                }

            return result

        finally:
            self.close_driver()


# 便捷函数
def test_account_login(platform, username, password, headless=True):
    """
    测试账号登录的便捷函数
    """
    tester = LoginTester(headless=headless)
    return tester.test_login(platform, username, password)
