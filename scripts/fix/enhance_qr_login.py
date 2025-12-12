#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强二维码登录功能
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
    print("增强二维码登录功能...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=10)

    # 创建增强的二维码登录文件
    enhanced_code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知乎二维码登录模块（增强版）
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
        """获取知乎扫码登录的二维码"""
        try:
            if not self.driver:
                if not self.init_browser():
                    return False, None, '浏览器初始化失败'

            logger.info('访问知乎登录页面...')
            self.driver.get(self.login_url)
            time.sleep(5)

            # 尝试点击二维码登录
            qr_tab_selectors = [
                'text:二维码登录',
                'text:扫码登录',
                '.SignFlow-qrcodeTab',
                'tab:二维码',
            ]

            for selector in qr_tab_selectors:
                try:
                    qr_tab = self.driver.ele(selector, timeout=2)
                    if qr_tab:
                        logger.info(f'找到二维码标签: {selector}')
                        qr_tab.click()
                        time.sleep(3)
                        break
                except:
                    continue

            # 扩展的二维码选择器
            qr_selectors = [
                '.qrcode-img img',
                '.SignFlow-qrcode img',
                'img[alt*="二维码"]',
                'img[alt*="QR"]',
                '.qrcode img',
                'img.qrcode',
                'canvas.qrcode',
                '.qrcode canvas',
                '#qrcode img',
                '[class*="qrcode"] img',
                'img[src*="qrcode"]',
                'img[src*="data:image"]',
            ]

            qr_img = None
            for selector in qr_selectors:
                try:
                    qr_img = self.driver.ele(selector, timeout=2)
                    if qr_img:
                        logger.info(f'找到二维码: {selector}')
                        break
                except:
                    continue

            # 如果没找到，截取登录区域
            if not qr_img:
                logger.warning('未找到二维码元素，尝试截取登录区域')
                login_selectors = ['.SignFlow', '.Login-content', '[class*="SignFlow"]']
                for selector in login_selectors:
                    try:
                        area = self.driver.ele(selector, timeout=2)
                        if area:
                            logger.info(f'截取登录区域: {selector}')
                            screenshot = area.get_screenshot(as_bytes=True)
                            qr_base64 = base64.b64encode(screenshot).decode('utf-8')
                            return True, qr_base64, '二维码获取成功'
                    except:
                        continue
                return False, None, '未找到二维码'

            # 获取二维码图片
            qr_src = qr_img.attr('src')
            if qr_src:
                if qr_src.startswith('data:image'):
                    qr_base64 = qr_src.split(',')[1]
                    logger.info('✓ 获取二维码(base64)')
                    return True, qr_base64, '二维码获取成功'
                elif qr_src.startswith('http'):
                    import requests
                    response = requests.get(qr_src)
                    qr_base64 = base64.b64encode(response.content).decode('utf-8')
                    logger.info('✓ 获取二维码(URL)')
                    return True, qr_base64, '二维码获取成功'

            # 截图方式
            screenshot = qr_img.get_screenshot(as_bytes=True)
            qr_base64 = base64.b64encode(screenshot).decode('utf-8')
            logger.info('✓ 获取二维码(截图)')
            return True, qr_base64, '二维码获取成功'

        except Exception as e:
            logger.error(f'获取二维码失败: {e}', exc_info=True)
            return False, None, str(e)

    def wait_for_login(self, timeout=120):
        """等待用户扫码登录"""
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    current_url = self.driver.url
                    if 'zhihu.com' in current_url and '/signin' not in current_url:
                        logger.info('✓ 登录成功!')
                        return True, '登录成功'

                    page_html = self.driver.html
                    if any(x in page_html for x in ['我的主页', '退出登录', '个人中心']):
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
            cookies = self.driver.cookies()
            cookie_file = os.path.join(self.cookies_dir, f'zhihu_{username}.json')
            with open(cookie_file, 'w', encoding='utf-8') as f:
                json.dump(list(cookies), f, ensure_ascii=False, indent=2)
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
    print("\n上传增强的二维码登录模块...")
    stdin, stdout, stderr = ssh.exec_command(f"cat > {DEPLOY_DIR}/backend/zhihu_auth/zhihu_qr_login.py << 'EOFFILE'\n{enhanced_code}\nEOFFILE")
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

    print("\n✓ 增强完成")
    print("\n改进内容:")
    print("1. 增加了更多二维码选择器")
    print("2. 如果找不到二维码元素，会截取整个登录区域")
    print("3. 增加了详细的日志输出")
    print("4. 优化了等待时间和超时处理")

    ssh.close()

if __name__ == '__main__':
    main()
