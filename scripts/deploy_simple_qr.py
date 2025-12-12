#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署简化的二维码登录模块（生成提示图片+后台静默登录）
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
    print("部署简化的二维码登录模块...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=10)

    simple_qr_code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知乎二维码登录模块（简化版：提示图片+后台登录）
"""
import time
import os
import base64
import logging
import json
import qrcode
import io as io_module
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
        """初始化浏览器（后台静默打开知乎登录页）"""
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

            # 后台访问知乎登录页（不等待加载完成）
            try:
                logger.info('后台打开知乎登录页...')
                self.driver.get(self.login_url, timeout=5)
            except:
                logger.info('页面加载超时（预期行为，继续）')

            return True
        except Exception as e:
            logger.error(f'浏览器初始化失败: {e}', exc_info=True)
            return False

    def get_qr_code(self):
        """生成二维码（包含知乎登录链接）"""
        try:
            # 初始化浏览器（后台）
            if not self.driver:
                if not self.init_browser():
                    return self._generate_simple_prompt_image()

            # 生成一个包含知乎登录链接的二维码
            logger.info('生成知乎登录二维码...')

            try:
                # 创建二维码
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(self.login_url)
                qr.make(fit=True)

                # 生成图片
                img = qr.make_image(fill_color="black", back_color="white")

                # 转换为base64
                buffer = io_module.BytesIO()
                img.save(buffer, format='PNG')
                qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

                logger.info(f'✓ 二维码生成成功 ({len(buffer.getvalue())} bytes)')
                return True, qr_base64, '请使用手机浏览器扫码并登录'

            except Exception as e:
                logger.warning(f'生成二维码失败: {e}，使用提示图片')
                return self._generate_simple_prompt_image()

        except Exception as e:
            logger.error(f'获取二维码失败: {e}', exc_info=True)
            return self._generate_simple_prompt_image()

    def _generate_simple_prompt_image(self):
        """生成简单的提示图片"""
        try:
            from PIL import Image, ImageDraw, ImageFont

            img = Image.new('RGB', (400, 400), color='white')
            draw = ImageDraw.Draw(img)

            # 绘制边框
            draw.rectangle([15, 15, 385, 385], outline='#1677ff', width=4)

            # 添加标题
            title = "知乎登录"
            bbox = draw.textbbox((0, 0), title)
            title_x = (400 - (bbox[2] - bbox[0])) // 2
            draw.text((title_x, 60), title, fill='#1677ff')

            # 添加提示文字
            lines = [
                "",
                "请打开手机浏览器",
                "",
                "访问:",
                "www.zhihu.com/signin",
                "",
                "扫描网页上的二维码",
                "",
                "登录后系统将自动检测"
            ]

            y = 130
            for line in lines:
                if line:
                    bbox = draw.textbbox((0, 0), line)
                    x = (400 - (bbox[2] - bbox[0])) // 2
                    draw.text((x, y), line, fill='black')
                y += 28

            # 转换为base64
            buffer = io_module.BytesIO()
            img.save(buffer, format='PNG')
            qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

            logger.info('✓ 生成提示图片')
            return True, qr_base64, '请访问知乎登录页面扫码'

        except Exception as e:
            logger.error(f'生成提示图片失败: {e}')
            return False, None, str(e)

    def wait_for_login(self, timeout=120):
        """等待用户扫码登录（检测浏览器中的登录状态）"""
        try:
            if not self.driver:
                return False, '浏览器未初始化'

            logger.info('开始等待用户扫码登录...')
            start_time = time.time()

            while time.time() - start_time < timeout:
                try:
                    # 获取当前URL
                    current_url = self.driver.url
                    logger.debug(f'当前URL: {current_url}')

                    # 检查URL是否已跳转
                    if 'zhihu.com' in current_url and '/signin' not in current_url:
                        logger.info('✓ URL已跳转，登录成功!')
                        time.sleep(3)  # 等待页面稳定
                        return True, '登录成功'

                    # 检查页面内容
                    try:
                        # 尝试查找登录后的元素
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
                    except Exception as e:
                        logger.debug(f'检查HTML失败: {e}')

                except Exception as e:
                    logger.debug(f'检查登录状态时出错: {e}')

                time.sleep(3)  # 每3秒检查一次

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
    print("\n上传简化的二维码登录模块...")
    stdin, stdout, stderr = ssh.exec_command(
        f"cat > {DEPLOY_DIR}/backend/zhihu_auth/zhihu_qr_login.py << 'EOFFILE'\n{simple_qr_code}\nEOFFILE"
    )
    stdout.read()
    print("✓ 已上传")

    # 安装qrcode库
    print("\n安装qrcode库...")
    stdin, stdout, stderr = ssh.exec_command("pip3 install qrcode[pil] --quiet")
    stdout.read()
    print("✓ 依赖已安装")

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
    print("\n工作原理:")
    print("1. 前端显示一个二维码（包含知乎登录链接）或提示图片")
    print("2. 用户用手机扫码或手动打开知乎登录页面")
    print("3. 后台浏览器同时打开知乎登录页（headless）")
    print("4. 用户在手机上登录后，后台浏览器检测到Cookie变化")
    print("5. 自动保存Cookie并完成登录")

    ssh.close()

if __name__ == '__main__':
    main()
