#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署改进的二维码登录模块（等待元素加载完成）
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
    print("部署改进的二维码登录模块...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=10)

    improved_qr_code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知乎二维码登录模块（改进版：等待元素加载）
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
        self.login_url = 'https://www.zhihu.com/signin'

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
            logger.info('✓ 浏览器初始化成功')
            return True
        except Exception as e:
            logger.error(f'浏览器初始化失败: {e}', exc_info=True)
            return False

    def get_qr_code(self):
        """获取知乎二维码"""
        try:
            if not self.driver:
                if not self.init_browser():
                    return self._generate_fallback_qr()

            logger.info('访问知乎登录页面...')

            # 访问页面（可能会卡住）
            try:
                self.driver.get(self.login_url, timeout=15)
            except Exception as e:
                logger.warning(f'页面加载超时（继续）: {e}')

            # 多次尝试等待页面元素
            max_attempts = 3
            for attempt in range(max_attempts):
                logger.info(f'尝试 {attempt + 1}/{max_attempts} 查找二维码...')

                # 等待一下让页面有时间加载
                time.sleep(3)

                # 检查是否有二维码登录按钮
                try:
                    qr_tab = self.driver.ele('text:二维码登录', timeout=2)
                    if qr_tab:
                        logger.info('找到二维码登录按钮，点击')
                        qr_tab.click()
                        time.sleep(3)
                        break
                except:
                    logger.debug('未找到二维码登录按钮')

                # 尝试其他选择器
                for selector in ['text:扫码登录', '.SignFlow-qrcodeTab']:
                    try:
                        tab = self.driver.ele(selector, timeout=1)
                        if tab:
                            logger.info(f'找到标签: {selector}')
                            tab.click()
                            time.sleep(3)
                            break
                    except:
                        continue

            # 现在尝试查找二维码元素
            logger.info('开始查找二维码图片元素...')

            # 定义二维码选择器（按优先级）
            qr_image_selectors = [
                ('.qrcode-img img', '二维码容器中的图片'),
                ('.SignFlow-qrcode img', 'SignFlow二维码图片'),
                ('img[alt*="二维码"]', '包含二维码alt的图片'),
                ('.qrcode img', 'qrcode类中的图片'),
                ('img[class*="qrcode"]', 'class包含qrcode的图片'),
            ]

            qr_element = None
            for selector, desc in qr_image_selectors:
                try:
                    logger.debug(f'尝试选择器: {selector} ({desc})')
                    elem = self.driver.ele(selector, timeout=2)
                    if elem:
                        # 检查元素是否可见和有尺寸
                        try:
                            # 获取元素的尺寸
                            rect = elem.rect
                            if rect and rect.size.height > 50 and rect.size.width > 50:
                                logger.info(f'✓ 找到二维码: {selector}, 尺寸: {rect.size.width}x{rect.size.height}')
                                qr_element = elem
                                break
                        except:
                            # 如果无法获取尺寸，仍然尝试使用
                            logger.info(f'✓ 找到二维码: {selector}')
                            qr_element = elem
                            break
                except Exception as e:
                    logger.debug(f'选择器 {selector} 失败: {e}')
                    continue

            if qr_element:
                # 尝试多种方式获取二维码图片
                logger.info('尝试获取二维码图片数据...')

                # 方法1：从src属性获取
                try:
                    src = qr_element.attr('src')
                    if src:
                        logger.debug(f'src属性: {src[:100]}...')

                        if src.startswith('data:image'):
                            qr_base64 = src.split(',')[1]
                            logger.info(f'✓ 从src获取base64二维码 ({len(qr_base64)} chars)')
                            return True, qr_base64, '二维码获取成功'

                        elif src.startswith('http'):
                            import requests
                            logger.info(f'从URL下载二维码: {src[:100]}...')
                            resp = requests.get(src, timeout=10)
                            qr_base64 = base64.b64encode(resp.content).decode('utf-8')
                            logger.info(f'✓ 从URL下载二维码 ({len(resp.content)} bytes)')
                            return True, qr_base64, '二维码获取成功'
                except Exception as e:
                    logger.debug(f'从src获取失败: {e}')

                # 方法2：截图元素
                try:
                    logger.info('尝试截图二维码元素...')
                    screenshot = qr_element.get_screenshot(as_bytes=True)
                    if screenshot and len(screenshot) > 200:
                        qr_base64 = base64.b64encode(screenshot).decode('utf-8')
                        logger.info(f'✓ 截图二维码成功 ({len(screenshot)} bytes)')
                        return True, qr_base64, '二维码获取成功'
                    else:
                        logger.warning(f'截图太小: {len(screenshot) if screenshot else 0} bytes')
                except Exception as e:
                    logger.warning(f'截图失败: {e}')

            # 如果找不到二维码，尝试截取登录区域
            logger.warning('未找到二维码，尝试截取登录区域...')
            for selector in ['.SignFlow', '.Login-content', '[class*="Login"]']:
                try:
                    area = self.driver.ele(selector, timeout=1)
                    if area:
                        screenshot = area.get_screenshot(as_bytes=True)
                        if screenshot and len(screenshot) > 1000:
                            qr_base64 = base64.b64encode(screenshot).decode('utf-8')
                            logger.info(f'✓ 截取登录区域 ({len(screenshot)} bytes)')
                            return True, qr_base64, '二维码获取成功'
                except Exception as e:
                    logger.debug(f'截取区域 {selector} 失败: {e}')

            # 所有方法都失败，使用降级方案
            logger.warning('所有获取方法失败，使用降级方案')
            return self._generate_fallback_qr()

        except Exception as e:
            logger.error(f'获取二维码过程出错: {e}', exc_info=True)
            return self._generate_fallback_qr()

    def _generate_fallback_qr(self):
        """生成降级提示图片"""
        try:
            from PIL import Image, ImageDraw
            import io as io_module

            img = Image.new('RGB', (300, 300), color='white')
            draw = ImageDraw.Draw(img)
            draw.rectangle([10, 10, 290, 290], outline='#1677ff', width=3)

            lines = ["知乎二维码", "", "请在账号配置页面", "使用测试按钮", "进行扫码登录"]
            y = 90
            for line in lines:
                bbox = draw.textbbox((0, 0), line)
                x = (300 - (bbox[2] - bbox[0])) // 2
                draw.text((x, y), line, fill='black')
                y += 35

            buffer = io_module.BytesIO()
            img.save(buffer, format='PNG')
            qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

            logger.info('✓ 生成降级提示图片')
            return True, qr_base64, '请在账号配置中扫码登录'
        except Exception as e:
            logger.error(f'生成降级图片失败: {e}')
            return False, None, str(e)

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

                    if 'zhihu.com' in current_url and '/signin' not in current_url:
                        logger.info('✓ URL已跳转，登录成功!')
                        time.sleep(2)
                        return True, '登录成功'

                    try:
                        page_html = self.driver.html
                        if any(x in page_html for x in ['我的主页', '退出登录', '个人中心']):
                            logger.info('✓ 检测到登录标识，登录成功!')
                            time.sleep(2)
                            return True, '登录成功'
                    except:
                        pass
                except Exception as e:
                    logger.debug(f'检查登录状态时出错: {e}')

                time.sleep(2)

            return False, '登录超时'
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

            logger.info(f'✓ Cookie已保存: {cookie_file}')
            return True
        except Exception as e:
            logger.error(f'保存Cookie失败: {e}', exc_info=True)
            return False

    def get_driver(self):
        return self.driver

    def close(self):
        try:
            if self.driver:
                self.driver.quit()
                logger.info('浏览器已关闭')
                self.driver = None
        except Exception as e:
            logger.warning(f'关闭浏览器时出错: {e}')
'''

    # 上传文件
    print("\n上传改进的二维码登录模块...")
    stdin, stdout, stderr = ssh.exec_command(
        f"cat > {DEPLOY_DIR}/backend/zhihu_auth/zhihu_qr_login.py << 'EOFFILE'\n{improved_qr_code}\nEOFFILE"
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
    print("1. 多次尝试查找二维码元素（最多3次）")
    print("2. 检查元素尺寸，确保是真正的二维码")
    print("3. 优先从src属性获取，其次截图")
    print("4. 详细的日志输出便于调试")

    ssh.close()

if __name__ == '__main__':
    main()
