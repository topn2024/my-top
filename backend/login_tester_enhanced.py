#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
账号登录测试模块 (增强版)
集成undetected-chromedriver降低验证码触发率
支持Cookie持久化登录
"""
import logging
import os
import json
import time
import random
from pathlib import Path

# 在模块级别设置DISPLAY环境变量
if 'DISPLAY' not in os.environ:
    os.environ['DISPLAY'] = ':99'

# 尝试导入undetected-chromedriver
try:
    import undetected_chromedriver as uc
    HAS_UNDETECTED = True
except ImportError:
    HAS_UNDETECTED = False
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logger = logging.getLogger(__name__)

class LoginTesterEnhanced:
    """网站登录测试器 (增强版 - 集成反检测)"""

    def __init__(self, headless=True, cookie_dir=None, use_undetected=True):
        """
        初始化登录测试器
        :param headless: 是否使用无头模式
        :param cookie_dir: Cookie存储目录
        :param use_undetected: 是否使用undetected-chromedriver（降低验证码触发率）
        """
        self.headless = headless
        self.use_undetected = use_undetected and HAS_UNDETECTED
        self.driver = None

        # 设置Cookie存储目录
        if cookie_dir is None:
            self.cookie_dir = Path(__file__).parent / 'cookies'
        else:
            self.cookie_dir = Path(cookie_dir)

        # 确保Cookie目录存在
        self.cookie_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Cookie directory: {self.cookie_dir}")

        if self.use_undetected:
            logger.info("✓ Using undetected-chromedriver (anti-detection mode)")
        else:
            logger.warning("× Using standard Selenium (higher captcha risk)")

    def init_driver(self):
        """初始化WebDriver - 支持反检测模式"""
        try:
            logger.info(f"Initializing WebDriver (headless={self.headless}, undetected={self.use_undetected})")

            # 方案1: 使用undetected-chromedriver (推荐)
            if self.use_undetected and HAS_UNDETECTED:
                self.driver = self._init_undetected_driver()
                if self.driver:
                    logger.info("✓ WebDriver initialized with anti-detection features")
                    return True

            # 方案2: 回退到标准Selenium
            logger.warning("Falling back to standard Selenium WebDriver")
            self.driver = self._init_standard_driver()
            if self.driver:
                logger.info("✓ WebDriver initialized (standard mode)")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}", exc_info=True)
            return False

    def _init_undetected_driver(self):
        """初始化undetected-chromedriver"""
        try:
            import platform
            system = platform.system()

            # 配置选项
            options = uc.ChromeOptions()

            # 基础选项
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')

            # 真实的User-Agent
            options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36')

            # Headless模式
            if self.headless:
                options.add_argument('--headless=new')  # 使用新版headless

            # Chrome二进制位置
            if system != 'Windows':
                options.binary_location = '/usr/bin/google-chrome'

            # ChromeDriver路径
            driver_path = None
            if system != 'Windows':
                if os.path.exists('/home/u_topn/chromedriver'):
                    driver_path = '/home/u_topn/chromedriver'

            # 创建driver
            driver = uc.Chrome(
                options=options,
                driver_executable_path=driver_path,
                version_main=143,  # Chrome主版本号
                use_subprocess=False,
                headless=self.headless
            )

            # 设置隐式等待
            driver.implicitly_wait(10)

            # 应用额外的反检测脚本
            self._apply_stealth_scripts(driver)

            return driver

        except Exception as e:
            logger.error(f"Failed to init undetected-chromedriver: {e}")
            return None

    def _init_standard_driver(self):
        """初始化标准Selenium WebDriver"""
        try:
            import platform
            system = platform.system()

            options = Options()

            # 基础选项
            if self.headless:
                options.add_argument('--headless')

            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36')

            # 反检测选项
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)

            # Chrome二进制位置
            if system == 'Windows':
                options.binary_location = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
            else:
                options.binary_location = '/usr/bin/google-chrome'

            # ChromeDriver路径
            driver_path = None
            if system != 'Windows':
                if os.path.exists('/home/u_topn/chromedriver'):
                    driver_path = '/home/u_topn/chromedriver'

            # 创建driver
            if driver_path:
                driver = webdriver.Chrome(executable_path=driver_path, options=options)
            else:
                driver = webdriver.Chrome(options=options)

            driver.implicitly_wait(10)

            # 应用反检测脚本
            self._apply_stealth_scripts(driver)

            return driver

        except Exception as e:
            logger.error(f"Failed to init standard driver: {e}")
            return None

    def _apply_stealth_scripts(self, driver):
        """应用反检测JavaScript脚本"""
        try:
            # 隐藏webdriver属性
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
                    window.chrome = {
                        runtime: {}
                    };
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

    # ==================== Cookie管理方法 ====================

    def _get_cookie_file(self, platform, username):
        """获取Cookie文件路径"""
        safe_username = username.replace('@', '_at_').replace('.', '_dot_')
        return self.cookie_dir / f"{platform}_{safe_username}.json"

    def save_cookies(self, platform, username):
        """保存当前会话的Cookie"""
        if not self.driver:
            logger.error("No active driver session")
            return False

        try:
            cookies = self.driver.get_cookies()
            cookie_file = self._get_cookie_file(platform, username)

            with open(cookie_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)

            logger.info(f"✓ Cookies saved to {cookie_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save cookies: {e}")
            return False

    def load_cookies(self, platform, username):
        """加载Cookie到当前会话"""
        if not self.driver:
            logger.error("No active driver session")
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
                    if 'expiry' in cookie:
                        cookie['expiry'] = int(cookie['expiry'])
                    if 'sameSite' in cookie and cookie['sameSite'] not in ['Strict', 'Lax', 'None']:
                        del cookie['sameSite']

                    self.driver.add_cookie(cookie)
                except Exception as e:
                    logger.debug(f"Failed to add cookie {cookie.get('name', 'unknown')}: {e}")
                    continue

            logger.info(f"✓ Cookies loaded from {cookie_file}")
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

    # ==================== 人类行为模拟 ====================

    def human_like_input(self, element, text, delay_range=(0.05, 0.15)):
        """模拟人类输入"""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(*delay_range))

    def human_like_click(self, element):
        """模拟人类点击"""
        try:
            # 先移动到元素
            actions = ActionChains(self.driver)
            actions.move_to_element(element).perform()
            time.sleep(random.uniform(0.1, 0.3))
            # 再点击
            element.click()
        except:
            # 回退到直接点击
            element.click()

    def random_delays(self):
        """随机延迟，模拟真人操作"""
        time.sleep(random.uniform(0.5, 1.5))

    # ==================== 知乎登录方法 ====================

    def test_zhihu_login(self, username, password, use_cookie=True, max_retries=2):
        """
        测试知乎登录 - 智能多策略

        策略:
        1. 优先使用Cookie登录（最快，无验证码）
        2. Cookie失败 -> 反检测模式密码登录
        3. 仍需验证码 -> 等待人工处理或重试

        :param username: 用户名
        :param password: 密码
        :param use_cookie: 是否优先使用Cookie
        :param max_retries: 最大重试次数
        :return: 登录结果字典
        """
        for attempt in range(max_retries):
            try:
                logger.info(f"=== Login Attempt {attempt + 1}/{max_retries} ===")

                # 初始化driver
                if not self.driver:
                    if not self.init_driver():
                        logger.error("Failed to initialize driver")
                        return {'success': False, 'message': 'WebDriver初始化失败'}

                # 策略1: 尝试Cookie登录
                if use_cookie and self.check_cookie_exists('知乎', username):
                    logger.info("Strategy 1: Trying cookie login...")

                    result = self._cookie_login(username)
                    if result['success']:
                        return result

                    logger.warning("Cookie login failed, falling back to password login")

                # 策略2: 密码登录（反检测模式）
                logger.info("Strategy 2: Password login with anti-detection...")

                result = self._password_login_zhihu(username, password)

                if result['success']:
                    # 保存Cookie供下次使用
                    if use_cookie:
                        self.save_cookies('知乎', username)
                    return result

                # 检查是否遇到验证码
                if 'captcha' in result.get('message', '').lower() or 'verification' in result.get('message', '').lower():
                    logger.warning(f"[Attempt {attempt + 1}] Captcha detected")

                    if attempt < max_retries - 1:
                        logger.info("Retrying with fresh session...")
                        self.quit_driver()
                        time.sleep(3)
                        continue
                    else:
                        # 最后一次尝试，等待人工处理
                        logger.info("Last attempt: waiting for manual captcha handling...")
                        return self._wait_for_manual_captcha(username, timeout=60)

            except Exception as e:
                logger.error(f"[Attempt {attempt + 1}] Error: {e}", exc_info=True)
                if attempt < max_retries - 1:
                    self.quit_driver()
                    time.sleep(3)
                    continue

        return {'success': False, 'message': '登录失败，已达最大重试次数'}

    def _cookie_login(self, username):
        """使用Cookie登录"""
        try:
            # 加载Cookie
            if not self.load_cookies('知乎', username):
                return {'success': False, 'message': 'Cookie加载失败'}

            # 刷新页面使Cookie生效
            self.driver.get('https://www.zhihu.com')
            time.sleep(2)

            # 检查是否登录成功
            current_url = self.driver.current_url
            if 'signin' not in current_url:
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
                        logger.info("✓ Cookie login successful!")
                        return {
                            'success': True,
                            'message': '使用Cookie登录成功',
                            'method': 'cookie',
                            'current_url': current_url
                        }
                    except:
                        continue

            return {'success': False, 'message': 'Cookie已过期'}

        except Exception as e:
            logger.error(f"Cookie login error: {e}")
            return {'success': False, 'message': f'Cookie登录异常: {str(e)}'}

    def _password_login_zhihu(self, username, password):
        """使用密码登录知乎（反检测模式）"""
        try:
            logger.info("Opening Zhihu login page...")
            self.driver.get('https://www.zhihu.com/signin')
            time.sleep(2)

            # 随机鼠标移动，模拟真人
            self.random_delays()

            # 切换到密码登录
            logger.info("Switching to password login mode...")
            password_btn_selectors = [
                (By.XPATH, "//div[@role='button' and text()='密码登录']"),
                (By.XPATH, "//div[contains(@class, 'SignFlow-tab') and text()='密码登录']"),
            ]

            password_btn = None
            for by, selector in password_btn_selectors:
                try:
                    password_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    break
                except:
                    continue

            if not password_btn:
                return {'success': False, 'message': '未找到密码登录按钮'}

            self.human_like_click(password_btn)
            time.sleep(1)
            logger.info("✓ Switched to password login mode")

            # 输入用户名（模拟真人输入）
            logger.info("Entering username...")
            username_input = self.driver.find_element(By.NAME, "username")
            self.human_like_input(username_input, username)
            logger.info("✓ Username entered")

            self.random_delays()

            # 输入密码
            logger.info("Entering password...")
            password_input = self.driver.find_element(By.NAME, "password")
            self.human_like_input(password_input, password)
            logger.info("✓ Password entered")

            self.random_delays()

            # 点击登录按钮
            logger.info("Clicking login button...")
            login_btn = self.driver.find_element(
                By.XPATH,
                "//button[@type='submit' and contains(@class, 'SignFlow-submitButton')]"
            )
            self.human_like_click(login_btn)
            logger.info("✓ Login button clicked")

            # 等待登录结果
            time.sleep(3)

            # 检查登录结果
            current_url = self.driver.current_url
            page_source = self.driver.page_source

            # 检查是否需要验证码
            if '验证' in page_source or 'captcha' in page_source.lower():
                logger.warning("⚠ Captcha detected")
                return {
                    'success': False,
                    'message': '登录需要验证码',
                    'current_url': current_url,
                    'needs_captcha': True
                }

            # 检查是否登录成功
            if 'signin' not in current_url:
                logger.info("✓ Password login successful!")
                return {
                    'success': True,
                    'message': '知乎登录成功',
                    'method': 'password',
                    'current_url': current_url
                }

            # 其他情况
            return {
                'success': False,
                'message': '登录失败，请检查账号密码',
                'current_url': current_url
            }

        except Exception as e:
            logger.error(f"Password login error: {e}", exc_info=True)
            return {'success': False, 'message': f'密码登录异常: {str(e)}'}

    def _wait_for_manual_captcha(self, username, timeout=60):
        """等待人工处理验证码"""
        logger.info(f"⏳ Waiting for manual captcha handling (timeout: {timeout}s)...")

        for i in range(timeout):
            time.sleep(1)

            try:
                # 检查是否登录成功
                if 'signin' not in self.driver.current_url:
                    logger.info("✓ Login successful after manual captcha!")
                    self.save_cookies('知乎', username)
                    return {
                        'success': True,
                        'message': '登录成功（人工验证码）',
                        'method': 'manual_captcha'
                    }
            except:
                pass

            if i % 10 == 0 and i > 0:
                logger.info(f"Still waiting... ({i}/{timeout}s)")

        return {
            'success': False,
            'message': '验证码处理超时'
        }

    def quit_driver(self):
        """关闭WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
                logger.debug("WebDriver closed")
            except Exception as e:
                logger.warning(f"Error closing driver: {e}")
            finally:
                self.driver = None

    def __del__(self):
        """析构函数"""
        self.quit_driver()


# 测试代码
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 创建测试器实例
    tester = LoginTesterEnhanced(headless=False, use_undetected=True)

    # 测试登录
    result = tester.test_zhihu_login(
        username="13751156900",
        password="your_password_here",
        use_cookie=True,
        max_retries=2
    )

    print("\n" + "="*80)
    print("Login Result:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("="*80)

    # 清理
    tester.quit_driver()
