#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署Canvas二维码提取版本（真实提取Canvas渲染的二维码）
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
    print("部署Canvas二维码提取版本...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=10)

    canvas_qr_code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知乎二维码登录模块（Canvas版：提取Canvas渲染的真实二维码）
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
    """安排延迟清理浏览器资源

    Args:
        driver: 浏览器驱动实例
        delay: 延迟时间（秒），默认3600秒（1小时）
    """
    def cleanup_task():
        try:
            time.sleep(delay)
            logger.info(f'定时清理：{delay}秒后开始清理浏览器资源...')
            if driver:
                driver.quit()
                logger.info('✓ 浏览器资源已自动清理')

                # 从全局列表中移除
                with _cleanup_lock:
                    if driver in _active_drivers:
                        _active_drivers.remove(driver)
        except Exception as e:
            logger.warning(f'定时清理时出错: {e}')

    # 启动后台清理线程
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


# 程序退出时自动清理
atexit.register(cleanup_all_drivers)


class ZhihuQRLogin:
    """知乎二维码登录类（Canvas版）"""

    def __init__(self, cookies_dir=None, auto_cleanup_delay=3600):
        """
        Args:
            cookies_dir: Cookie保存目录
            auto_cleanup_delay: 自动清理延迟时间（秒），默认3600秒（1小时）
        """
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

            self.driver = ChromiumPage(addr_or_opts=co)

            # 添加到全局跟踪
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
        """获取知乎二维码（Canvas版：提取Canvas元素）"""
        max_attempts = 3  # 3次尝试

        try:
            if not self.driver:
                if not self.init_browser():
                    logger.error('浏览器初始化失败，清理资源')
                    self.close()
                    return False, None, '浏览器初始化失败'

            # 多次尝试获取二维码
            for attempt in range(max_attempts):
                logger.info(f'=== 尝试 {attempt + 1}/{max_attempts} 获取二维码 ===')

                try:
                    if attempt == 0:
                        logger.info('访问知乎登录页面...')
                        self.driver.get(self.login_url, timeout=10)
                    else:
                        logger.info('刷新页面重试...')
                        self.driver.refresh()

                    # 等待页面加载
                    time.sleep(3)
                except Exception as e:
                    logger.warning(f'页面加载超时（继续）: {e}')
                    time.sleep(2)

                # 尝试点击二维码登录标签
                for selector in ['text:二维码登录', 'text:扫码登录', '.SignFlow-qrcodeTab']:
                    try:
                        tab = self.driver.ele(selector, timeout=1.5)
                        if tab:
                            logger.info(f'找到并点击: {selector}')
                            tab.click()
                            time.sleep(2)
                            break
                    except Exception as e:
                        logger.debug(f'未找到 {selector}: {e}')

                # 关键：查找Canvas二维码元素
                logger.info('查找Canvas二维码元素...')
                canvas_selectors = [
                    'canvas.Qrcode-qrcode',  # class="Qrcode-qrcode"
                    'canvas[alt="二维码"]',   # alt="二维码"
                    'canvas[class*="Qrcode"]',  # class包含Qrcode
                    'canvas[class*="qrcode"]',  # class包含qrcode
                ]

                qr_canvas = None
                for selector in canvas_selectors:
                    try:
                        logger.debug(f'尝试选择器: {selector}')
                        canvas = self.driver.ele(selector, timeout=2)
                        if canvas:
                            logger.info(f'✓ 找到Canvas二维码: {selector}')
                            qr_canvas = canvas
                            break
                    except Exception as e:
                        logger.debug(f'选择器 {selector} 失败: {e}')

                if qr_canvas:
                    # 截图Canvas元素
                    try:
                        logger.info('截图Canvas二维码...')
                        screenshot = qr_canvas.get_screenshot(as_bytes=True)

                        if screenshot and len(screenshot) > 200:
                            qr_base64 = base64.b64encode(screenshot).decode('utf-8')
                            logger.info(f'✓ Canvas二维码截图成功 ({len(screenshot)} bytes)')
                            return True, qr_base64, '二维码获取成功'
                        else:
                            logger.warning(f'Canvas截图太小: {len(screenshot) if screenshot else 0} bytes')
                    except Exception as e:
                        logger.warning(f'Canvas截图失败: {e}')

                # 如果找不到Canvas，尝试查找包含二维码的容器并截图
                logger.warning('未找到Canvas二维码，尝试截取二维码容器...')
                container_selectors = [
                    '.Qrcode',
                    '[class*="Qrcode"]',
                    '[class*="qrcode"]',
                ]

                for selector in container_selectors:
                    try:
                        container = self.driver.ele(selector, timeout=1.5)
                        if container:
                            screenshot = container.get_screenshot(as_bytes=True)
                            if screenshot and len(screenshot) > 500:
                                qr_base64 = base64.b64encode(screenshot).decode('utf-8')
                                logger.info(f'✓ 截取二维码容器成功 ({len(screenshot)} bytes)')
                                return True, qr_base64, '二维码获取成功'
                    except Exception as e:
                        logger.debug(f'容器 {selector} 截图失败: {e}')

                if attempt < max_attempts - 1:
                    logger.warning('未找到二维码，准备刷新页面重试...')
                    time.sleep(1)

            # 所有尝试失败，立即清理资源
            logger.error('无法获取二维码（3次尝试失败），立即清理资源')
            self.close()
            return False, None, '暂时无法获取二维码，请稍后重试'

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
        """立即关闭浏览器（取消自动清理）"""
        try:
            if self.driver:
                # 从全局列表中移除
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
    print("\n上传Canvas二维码提取模块...")
    stdin, stdout, stderr = ssh.exec_command(
        f"cat > {DEPLOY_DIR}/backend/zhihu_auth/zhihu_qr_login.py << 'EOFFILE'\n{canvas_qr_code}\nEOFFILE"
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
    print("\n改进内容:")
    print("1. 识别Canvas元素：知乎二维码使用Canvas渲染，class='Qrcode-qrcode'")
    print("2. Canvas截图：直接截图Canvas元素获取真实二维码")
    print("3. 多重选择器：canvas.Qrcode-qrcode / canvas[alt='二维码'] 等")
    print("4. 容器降级：如果找不到Canvas，尝试截取包含二维码的容器")
    print("5. 3次重试机制：每次失败后刷新页面重试")
    print("6. 失败立即清理：所有尝试失败后立即释放浏览器资源")

    ssh.close()

if __name__ == '__main__':
    main()
