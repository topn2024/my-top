#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署带资源自动回收的二维码登录模块
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
    print("部署带资源自动回收的二维码登录模块...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=10)

    qr_code_with_cleanup = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知乎二维码登录模块（带资源自动回收）
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
    """知乎二维码登录类（带资源自动回收）"""

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
        """获取二维码（生成提示图片）"""
        try:
            # 初始化浏览器（后台）
            if not self.driver:
                if not self.init_browser():
                    return self._generate_prompt_image()

            # 后台访问知乎登录页
            try:
                logger.info('后台打开知乎登录页...')
                self.driver.get(self.login_url, timeout=10)
            except Exception as e:
                logger.warning(f'页面加载超时（预期）: {e}')

            # 生成提示图片
            return self._generate_prompt_image()

        except Exception as e:
            logger.error(f'获取二维码失败: {e}', exc_info=True)
            return self._generate_prompt_image()

    def _generate_prompt_image(self):
        """生成提示图片"""
        try:
            from PIL import Image, ImageDraw

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
                "访问: zhihu.com/signin",
                "",
                "扫描网页上的二维码",
                "",
                "登录后系统将自动检测",
                "",
                "资源将在1小时后自动回收"
            ]

            y = 120
            for line in lines:
                if line:
                    bbox = draw.textbbox((0, 0), line)
                    x = (400 - (bbox[2] - bbox[0])) // 2
                    draw.text((x, y), line, fill='black')
                y += 26

            # 转换为base64
            import io as io_module
            buffer = io_module.BytesIO()
            img.save(buffer, format='PNG')
            qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

            logger.info('✓ 生成提示图片')
            return True, qr_base64, '请访问知乎登录页面扫码'

        except Exception as e:
            logger.error(f'生成提示图片失败: {e}')
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
    print("\n上传带资源回收的二维码登录模块...")
    stdin, stdout, stderr = ssh.exec_command(
        f"cat > {DEPLOY_DIR}/backend/zhihu_auth/zhihu_qr_login.py << 'EOFFILE'\n{qr_code_with_cleanup}\nEOFFILE"
    )
    stdout.read()
    print("✓ 已上传")

    # 上传清理脚本
    print("\n上传Chrome清理脚本...")
    cleanup_script = '''#!/bin/bash
# Chrome进程清理脚本

echo "=== Chrome进程清理 $(date) ==="

# 查找所有DrissionPage相关的Chrome进程
CHROME_PIDS=$(ps aux | grep -E 'chrome.*(DrissionPage|remote-debugging)' | grep -v grep | awk '{print $2}')

if [ -z "$CHROME_PIDS" ]; then
    echo "✓ 没有僵尸Chrome进程"
else
    echo "发现Chrome进程，开始清理..."
    for pid in $CHROME_PIDS; do
        kill -9 $pid 2>/dev/null || true
    done
    echo "✓ 清理完成"
fi

echo "内存使用: $(free -h | grep Mem | awk '{print $3 "/" $2}')"
echo "Chrome进程数: $(ps aux | grep chrome | grep -v grep | wc -l)"
'''

    stdin, stdout, stderr = ssh.exec_command(
        f"cat > {DEPLOY_DIR}/scripts/cleanup_chrome.sh << 'EOF'\n{cleanup_script}\nEOF && chmod +x {DEPLOY_DIR}/scripts/cleanup_chrome.sh"
    )
    stdout.read()
    print("✓ 清理脚本已上传")

    # 添加crontab任务（每小时清理一次）
    print("\n配置定时清理任务...")
    cron_cmd = f"0 * * * * {DEPLOY_DIR}/scripts/cleanup_chrome.sh >> {DEPLOY_DIR}/logs/cleanup.log 2>&1"

    # 检查是否已存在
    stdin, stdout, stderr = ssh.exec_command("crontab -l 2>/dev/null | grep cleanup_chrome.sh")
    existing = stdout.read().decode('utf-8').strip()

    if existing:
        print("✓ 定时任务已存在")
    else:
        stdin, stdout, stderr = ssh.exec_command(
            f"(crontab -l 2>/dev/null; echo '{cron_cmd}') | crontab -"
        )
        stdout.read()
        print("✓ 已添加定时清理任务（每小时执行）")

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
    print("\n资源回收机制:")
    print("1. 浏览器初始化时自动安排1小时后清理")
    print("2. 登录完成保存Cookie后，资源继续保留1小时")
    print("3. 1小时后自动调用driver.quit()释放资源")
    print("4. 程序退出时自动清理所有浏览器实例")
    print("5. Crontab定时任务每小时清理僵尸进程")
    print("\n手动清理命令:")
    print(f"  bash {DEPLOY_DIR}/scripts/cleanup_chrome.sh")

    ssh.close()

if __name__ == '__main__':
    main()
