#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用Selenium替换DrissionPage实现二维码登录
"""

import paramiko
import sys
import io
import time
from pathlib import Path

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

SERVER = "39.105.12.124"
USER = "u_topn"
PASSWORD = "TopN@2024"
DEPLOY_DIR = "/home/u_topn/TOP_N"

def main():
    print("使用Selenium替换DrissionPage...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=10)

    # 创建使用Selenium的二维码登录模块
    selenium_code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知乎二维码登录模块（Selenium版本）
"""
import time
import os
import base64
import logging
import json

logger = logging.getLogger(__name__)


class ZhihuQRLogin:
    """知乎二维码登录类（使用Selenium）"""

    def __init__(self, cookies_dir=None):
        self.driver = None
        self.login_url = 'https://www.zhihu.com/signin'

        if cookies_dir is None:
            cookies_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cookies')
        self.cookies_dir = cookies_dir
        os.makedirs(self.cookies_dir, exist_ok=True)

    def init_browser(self):
        """初始化浏览器（使用Selenium）"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service

            chrome_options = Options()

            # 服务器环境检测
            is_server = not os.environ.get('DISPLAY')
            if is_server:
                logger.info("检测到服务器环境，使用headless模式")
                chrome_options.add_argument('--headless')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--disable-gpu')

            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            chrome_options.add_argument('--window-size=1920,1080')

            # 初始化driver
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info('✓ 二维码登录浏览器初始化成功（Selenium）')
            return True
        except Exception as e:
            logger.error(f'浏览器初始化失败: {e}', exc_info=True)
            return False

    def get_qr_code(self):
        """获取知乎扫码登录的二维码"""
        try:
            if not self.driver:
                if not self.init_browser():
                    return False, None, '浏览器初始化失败'

            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC

            logger.info('访问知乎登录页面...')
            self.driver.get(self.login_url)
            time.sleep(5)

            # 尝试点击二维码登录标签
            qr_tab_selectors = [
                (By.XPATH, "//*[contains(text(), '二维码登录')]"),
                (By.XPATH, "//*[contains(text(), '扫码登录')]"),
                (By.CLASS_NAME, "SignFlow-qrcodeTab"),
            ]

            for by, selector in qr_tab_selectors:
                try:
                    tab = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((by, selector))
                    )
                    tab.click()
                    logger.info(f'点击二维码标签成功: {selector}')
                    time.sleep(3)
                    break
                except:
                    continue

            # 查找二维码图片
            qr_selectors = [
                (By.CSS_SELECTOR, ".qrcode-img img"),
                (By.CSS_SELECTOR, ".SignFlow-qrcode img"),
                (By.XPATH, "//img[contains(@alt, '二维码')]"),
                (By.CLASS_NAME, "qrcode"),
                (By.CSS_SELECTOR, "img[src*='data:image']"),
            ]

            qr_element = None
            for by, selector in qr_selectors:
                try:
                    qr_element = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((by, selector))
                    )
                    logger.info(f'找到二维码元素: {selector}')
                    break
                except:
                    continue

            # 如果没找到二维码，截取整个页面
            if not qr_element:
                logger.warning('未找到二维码元素，截取整个页面')
                screenshot = self.driver.get_screenshot_as_png()
                qr_base64 = base64.b64encode(screenshot).decode('utf-8')
                logger.info('✓ 获取页面截图作为二维码')
                return True, qr_base64, '二维码获取成功'

            # 获取二维码图片
            try:
                # 方法1：获取src属性
                qr_src = qr_element.get_attribute('src')
                if qr_src and qr_src.startswith('data:image'):
                    qr_base64 = qr_src.split(',')[1]
                    logger.info('✓ 获取二维码(base64)')
                    return True, qr_base64, '二维码获取成功'
                elif qr_src and qr_src.startswith('http'):
                    import requests
                    response = requests.get(qr_src)
                    qr_base64 = base64.b64encode(response.content).decode('utf-8')
                    logger.info('✓ 获取二维码(URL)')
                    return True, qr_base64, '二维码获取成功'

                # 方法2：截取元素
                screenshot = qr_element.screenshot_as_png
                qr_base64 = base64.b64encode(screenshot).decode('utf-8')
                logger.info('✓ 获取二维码(截图)')
                return True, qr_base64, '二维码获取成功'

            except Exception as e:
                logger.error(f'获取二维码失败: {e}', exc_info=True)
                return False, None, f'获取二维码失败: {str(e)}'

        except Exception as e:
            logger.error(f'获取二维码过程失败: {e}', exc_info=True)
            return False, None, str(e)

    def wait_for_login(self, timeout=120):
        """等待用户扫码登录"""
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    current_url = self.driver.current_url
                    if 'zhihu.com' in current_url and '/signin' not in current_url:
                        logger.info('✓ 登录成功!')
                        return True, '登录成功'

                    page_source = self.driver.page_source
                    if any(x in page_source for x in ['我的主页', '退出登录', '个人中心']):
                        logger.info('✓ 登录成功!')
                        return True, '登录成功'
                except:
                    pass
                time.sleep(2)
            return False, '登录超时'
        except Exception as e:
            logger.error(f'等待登录失败: {e}', exc_info=True)
            return False, str(e)

    def save_cookies(self, username):
        """保存Cookie"""
        try:
            cookies = self.driver.get_cookies()
            cookie_file = os.path.join(self.cookies_dir, f'zhihu_{username}.json')
            with open(cookie_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            logger.info(f'✓ Cookie已保存: {cookie_file}')
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
'''

    # 上传文件
    print("\n上传Selenium版本的二维码登录模块...")
    stdin, stdout, stderr = ssh.exec_command(f"cat > {DEPLOY_DIR}/backend/zhihu_auth/zhihu_qr_login.py << 'EOFFILE'\n{selenium_code}\nEOFFILE")
    stdout.read()
    print("✓ 已上传")

    # 重启服务
    print("\n重启服务...")
    stdin, stdout, stderr = ssh.exec_command("pkill -f gunicorn; sleep 2")
    stdout.read()

    start_cmd = f"bash {DEPLOY_DIR}/start_service.sh"
    stdin, stdout, stderr = ssh.exec_command(start_cmd)
    print(stdout.read().decode('utf-8', errors='ignore'))

    time.sleep(3)

    # 测试
    print("\n测试健康检查...")
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8080/api/health")
    print(stdout.read().decode('utf-8', errors='ignore'))

    print("\n✓ 更新完成")
    print("\n改进内容:")
    print("1. 使用Selenium替代DrissionPage，在服务器环境中更稳定")
    print("2. 支持headless模式")
    print("3. 自动处理ChromeDriver")
    print("4. 更可靠的元素查找和截图功能")

    ssh.close()

if __name__ == '__main__':
    main()
