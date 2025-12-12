#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署截图版二维码登录模块（直接截取登录页面上的二维码）
"""

import paramiko
import sys
import io
import time

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

SERVER = "39.105.12.124"
USER = "u_topn"
PASSWORD = "TopN@2024"
DEPLOY_DIR = "/home/u_topn/TOP_N"

def main():
    print("部署截图版二维码登录模块...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=10)

    screenshot_qr_code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知乎二维码登录模块（截图版：直接截取页面上的二维码区域）
"""
import time
import os
import base64
import logging
import json
import threading
import atexit
from DrissionPage import ChromiumPage, ChromiumOptions

logger = logging.getLogger(__name__)

# 全局浏览器实例跟踪
_active_drivers = []
_cleanup_lock = threading.Lock()


def schedule_cleanup(driver, delay=3600):
    """安排延迟清理浏览器资源"""
    def cleanup_task():
        try:
            time.sleep(delay)
            logger.info(f'定时清理：{delay}秒后开始清理浏览器资源...')
            if driver:
                driver.quit()
                logger.info('✓ 浏览器资源已自动清理')
                with _cleanup_lock:
                    if driver in _active_drivers:
                        _active_drivers.remove(driver)
        except Exception as e:
            logger.warning(f'定时清理时出错: {e}')

    cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
    cleanup_thread.start()
    logger.info(f'✓ 已安排{delay}秒后自动清理浏览器资源')


def cleanup_all_drivers():
    """清理所有活跃的浏览器实例"""
    with _cleanup_lock:
        for driver in _active_drivers[:]:
            try:
                driver.quit()
                logger.info('✓ 清理浏览器实例')
            except:
                pass
        _active_drivers.clear()


atexit.register(cleanup_all_drivers)


class ZhihuQRLogin:
    """知乎二维码登录类（截图版）"""

    def __init__(self, cookies_dir=None, auto_cleanup_delay=3600):
        self.driver = None
        self.login_url = 'https://www.zhihu.com/signin'
        self.auto_cleanup_delay = auto_cleanup_delay

        if cookies_dir is None:
            cookies_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cookies')
        self.cookies_dir = cookies_dir
        os.makedirs(self.cookies_dir, exist_ok=True)

    def init_browser(self):
        """初始化浏览器"""
        try:
            co = ChromiumOptions()
            co.auto_port(True)

            # Headless模式
            co.headless(True)
            co.set_argument('--no-sandbox')
            co.set_argument('--disable-dev-shm-usage')
            co.set_argument('--disable-gpu')
            co.set_argument('--disable-blink-features=AutomationControlled')
            co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

            # 设置窗口大小，确保二维码完全可见
            co.set_argument('--window-size=1200,900')

            self.driver = ChromiumPage(addr_or_opts=co)

            with _cleanup_lock:
                _active_drivers.append(self.driver)

            logger.info('✓ 浏览器初始化成功')

            # 安排自动清理
            schedule_cleanup(self.driver, self.auto_cleanup_delay)

            return True
        except Exception as e:
            logger.error(f'浏览器初始化失败: {e}', exc_info=True)
            return False

    def get_qr_code(self):
        """获取知乎二维码（截图方式）"""
        try:
            if not self.driver:
                if not self.init_browser():
                    logger.error('浏览器初始化失败，清理资源')
                    self.close()
                    return False, None, '浏览器初始化失败'

            logger.info('访问知乎登录页面...')

            # 访问登录页
            try:
                self.driver.get(self.login_url, timeout=15)
            except Exception as e:
                logger.warning(f'页面加载超时（继续）: {e}')

            # 等待页面加载（重要：让JavaScript渲染二维码）
            logger.info('等待页面加载和二维码渲染...')
            time.sleep(5)  # 5秒等待，确保二维码完全渲染

            # 尝试点击二维码登录标签
            logger.info('尝试切换到二维码登录...')
            for selector in ['text:二维码登录', 'text:扫码登录']:
                try:
                    tab = self.driver.ele(selector, timeout=2)
                    if tab:
                        logger.info(f'找到并点击: {selector}')
                        tab.click()
                        time.sleep(3)  # 点击后等待二维码显示
                        break
                except Exception as e:
                    logger.debug(f'未找到 {selector}: {e}')

            # 再等待一下确保二维码完全显示
            time.sleep(2)

            # 方法1：尝试查找并截取二维码容器
            logger.info('查找二维码容器元素...')
            qr_container_selectors = [
                '.Qrcode',              # 二维码容器
                '[class*="Qrcode"]',    # class包含Qrcode
                '[class*="qrcode"]',    # class包含qrcode（小写）
                '.SignFlow-qrcode',     # SignFlow二维码
            ]

            for selector in qr_container_selectors:
                try:
                    logger.debug(f'尝试选择器: {selector}')
                    container = self.driver.ele(selector, timeout=2)
                    if container:
                        logger.info(f'✓ 找到二维码容器: {selector}')

                        # 截图容器
                        screenshot = container.get_screenshot(as_bytes=True)

                        if screenshot and len(screenshot) > 500:
                            qr_base64 = base64.b64encode(screenshot).decode('utf-8')
                            logger.info(f'✓ 二维码截图成功 ({len(screenshot)} bytes)')
                            return True, qr_base64, '二维码获取成功'
                        else:
                            logger.warning(f'截图太小: {len(screenshot) if screenshot else 0} bytes')
                except Exception as e:
                    logger.debug(f'选择器 {selector} 失败: {e}')

            # 方法2：截取整个登录区域（更大范围）
            logger.info('尝试截取整个登录区域...')
            login_area_selectors = [
                '.SignFlow',
                '.Login-content',
                '[class*="SignFlow"]',
                '[class*="Login"]',
            ]

            for selector in login_area_selectors:
                try:
                    area = self.driver.ele(selector, timeout=2)
                    if area:
                        logger.info(f'找到登录区域: {selector}')
                        screenshot = area.get_screenshot(as_bytes=True)

                        if screenshot and len(screenshot) > 1000:
                            qr_base64 = base64.b64encode(screenshot).decode('utf-8')
                            logger.info(f'✓ 登录区域截图成功 ({len(screenshot)} bytes)')
                            return True, qr_base64, '二维码获取成功'
                except Exception as e:
                    logger.debug(f'截取区域 {selector} 失败: {e}')

            # 方法3：截取整个页面（最后的备用方案）
            logger.warning('无法定位二维码，截取整个页面...')
            try:
                screenshot = self.driver.get_screenshot(as_bytes=True)
                if screenshot and len(screenshot) > 2000:
                    qr_base64 = base64.b64encode(screenshot).decode('utf-8')
                    logger.info(f'✓ 整页截图成功 ({len(screenshot)} bytes)')
                    return True, qr_base64, '页面截图（包含二维码）'
            except Exception as e:
                logger.error(f'整页截图失败: {e}')

            # 所有方法都失败
            logger.error('所有截图方法失败，清理资源')
            self.close()
            return False, None, '无法获取二维码截图'

        except Exception as e:
            logger.error(f'获取二维码出错: {e}，清理资源', exc_info=True)
            self.close()
            return False, None, f'获取失败: {str(e)}'

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

                    # 检查URL是否已跳转
                    if 'zhihu.com' in current_url and '/signin' not in current_url:
                        logger.info('✓ URL已跳转，登录成功!')
                        time.sleep(3)
                        return True, '登录成功'

                    # 检查页面内容
                    try:
                        if self.driver.ele('text:我的主页', timeout=0.5):
                            logger.info('✓ 找到"我的主页"，登录成功!')
                            time.sleep(2)
                            return True, '登录成功'
                    except:
                        pass

                    try:
                        page_html = self.driver.html
                        if any(x in page_html for x in ['退出登录', '个人中心', 'class="Profile-']):
                            logger.info('✓ 检测到登录标识，登录成功!')
                            time.sleep(2)
                            return True, '登录成功'
                    except:
                        pass

                except Exception as e:
                    logger.debug(f'检查登录状态时出错: {e}')

                time.sleep(3)

            return False, '登录超时，请重试'

        except Exception as e:
            logger.error(f'等待登录失败: {e}', exc_info=True)
            return False, str(e)

    def save_cookies(self, username):
        """保存Cookie"""
        try:
            if not self.driver:
                return False

            cookies = self.driver.cookies()
            cookie_file = os.path.join(self.cookies_dir, f'zhihu_{username}.json')

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
            logger.info(f'浏览器资源将在{self.auto_cleanup_delay}秒后自动回收')
            return True

        except Exception as e:
            logger.error(f'保存Cookie失败: {e}', exc_info=True)
            return False

    def get_driver(self):
        return self.driver

    def close(self):
        """立即关闭浏览器"""
        try:
            if self.driver:
                with _cleanup_lock:
                    if self.driver in _active_drivers:
                        _active_drivers.remove(self.driver)

                self.driver.quit()
                logger.info('浏览器已手动关闭')
                self.driver = None
        except Exception as e:
            logger.warning(f'关闭浏览器时出错: {e}')
'''

    # 上传文件
    print("\n上传截图版二维码登录模块...")
    stdin, stdout, stderr = ssh.exec_command(
        f"cat > {DEPLOY_DIR}/backend/zhihu_auth/zhihu_qr_login.py << 'EOFFILE'\n{screenshot_qr_code}\nEOFFILE"
    )
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

    print("\n✓ 部署完成")
    print("\n实现方式:")
    print("1. 访问知乎登录页面")
    print("2. 等待页面完全加载（5秒）")
    print("3. 点击'二维码登录'标签")
    print("4. 等待二维码渲染完成（3秒）")
    print("5. 直接截取二维码容器/登录区域的屏幕截图")
    print("6. 将截图base64编码后返回给前端")
    print("7. 前端显示截图中的二维码供用户扫码")
    print("\n优点:")
    print("- 不需要提取Canvas内容")
    print("- 不需要重新绘制二维码")
    print("- 获取的是页面上实际渲染的二维码图像")
    print("- 实现简单稳定")

    ssh.close()

if __name__ == '__main__':
    main()
