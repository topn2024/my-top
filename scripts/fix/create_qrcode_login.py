#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建二维码登录模块
"""
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

QRCODE_LOGIN_CODE = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知乎二维码登录模块
"""
import time
import base64
import logging

logger = logging.getLogger(__name__)

class ZhihuQRCodeLogin:
    """知乎二维码登录"""

    def __init__(self, mode='drission'):
        self.mode = mode
        self.page = None

    def init_browser(self):
        """初始化浏览器"""
        try:
            from DrissionPage import ChromiumPage, ChromiumOptions
            co = ChromiumOptions()
            co.headless(False)  # 需要可见才能正确加载二维码
            co.set_argument('--disable-blink-features=AutomationControlled')
            self.page = ChromiumPage(addr_or_opts=co)
            logger.info("DrissionPage initialized for QR login")
            return True
        except Exception as e:
            logger.error(f"DrissionPage initialization failed: {e}")
            return False

    def get_qrcode(self):
        """获取知乎登录二维码"""
        try:
            if not self.page and not self.init_browser():
                return {'success': False, 'message': 'Browser init failed'}

            self.page.get('https://www.zhihu.com/signin')
            time.sleep(2)

            # 点击二维码登录
            try:
                qr_tab = self.page.ele('text:二维码登录', timeout=5)
                if qr_tab:
                    qr_tab.click()
                    time.sleep(2)
                    logger.info("Switched to QR code login")
            except:
                logger.warning("QR tab not found")

            # 截取整个登录区域
            time.sleep(1)
            screenshot = self.page.get_screenshot(as_bytes='png')
            qrcode_base64 = base64.b64encode(screenshot).decode('utf-8')

            return {
                'success': True,
                'qrcode_base64': qrcode_base64,
                'message': 'QR code obtained'
            }

        except Exception as e:
            logger.error(f"Get QR code failed: {e}", exc_info=True)
            return {'success': False, 'message': str(e)}

    def check_login_status(self):
        """检查扫码登录状态"""
        try:
            current_url = self.page.url

            if 'signin' not in current_url:
                logger.info("QR login success")
                return {'success': True, 'status': 'success', 'message': '登录成功'}

            page_html = self.page.html
            if '已扫描' in page_html or '确认登录' in page_html:
                return {'success': True, 'status': 'scanned', 'message': '已扫描'}
            elif '已过期' in page_html or '已失效' in page_html:
                return {'success': True, 'status': 'expired', 'message': '已过期'}
            else:
                return {'success': True, 'status': 'waiting', 'message': '等待扫码'}

        except Exception as e:
            logger.error(f"Check status failed: {e}")
            return {'success': False, 'status': 'error', 'message': str(e)}

    def save_cookies(self, username):
        """保存Cookie"""
        try:
            import json
            import os

            cookies_dir = os.path.join(os.path.dirname(__file__), 'cookies')
            os.makedirs(cookies_dir, exist_ok=True)

            cookies = self.page.cookies()
            cookie_list = []
            for cookie in cookies:
                cookie_list.append({
                    'name': cookie.get('name'),
                    'value': cookie.get('value'),
                    'domain': cookie.get('domain'),
                    'path': cookie.get('path', '/')
                })

            cookie_file = os.path.join(cookies_dir, f'zhihu_{username}.json')
            with open(cookie_file, 'w', encoding='utf-8') as f:
                json.dump(cookie_list, f, ensure_ascii=False, indent=2)

            logger.info(f"Cookies saved: {cookie_file}")
            return {'success': True, 'message': 'Cookie saved'}

        except Exception as e:
            logger.error(f"Save cookies failed: {e}")
            return {'success': False, 'message': str(e)}

    def close(self):
        """关闭浏览器"""
        try:
            if self.page:
                self.page.quit()
        except:
            pass
'''

def main():
    try:
        print("="*80)
        print("创建二维码登录模块")
        print("="*80)

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("✓ SSH连接成功\n")

        # 创建二维码登录模块文件
        print("[1/1] 创建 qrcode_login.py...")

        # 使用SFTP上传文件
        sftp = ssh.open_sftp()
        remote_path = '/home/u_topn/TOP_N/backend/qrcode_login.py'

        with sftp.open(remote_path, 'w') as f:
            f.write(QRCODE_LOGIN_CODE)

        sftp.close()
        print("✓ qrcode_login.py 已创建")

        # 设置权限
        stdin, stdout, stderr = ssh.exec_command(f"chmod +x {remote_path}")
        stdout.read()

        print("\n" + "="*80)
        print("✅ 二维码登录模块创建完成")
        print("="*80)

        ssh.close()
        return True

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()
