#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知乎二维码登录模块
使用API方式实现知乎扫码登录
"""
import time
import os
import sys
import base64
import logging
import json
import requests
import qrcode
from io import BytesIO
from logging.handlers import RotatingFileHandler

# 添加backend目录到path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)


def setup_qr_login_logger():
    """为二维码登录模块设置日志"""
    qr_logger = logging.getLogger(__name__)

    # 避免重复配置
    if qr_logger.handlers:
        return qr_logger

    qr_logger.setLevel(logging.INFO)
    qr_logger.propagate = False

    # 日志目录
    log_dir = os.path.join(BACKEND_DIR, '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)

    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-5s | QR_LOGIN | %(name)-20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 写入all.log
    all_log_file = os.path.join(log_dir, 'all.log')
    all_handler = RotatingFileHandler(
        all_log_file,
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    all_handler.setLevel(logging.DEBUG)
    all_handler.setFormatter(formatter)
    qr_logger.addHandler(all_handler)

    # 写入zhihu日志
    zhihu_log_file = os.path.join(log_dir, 'zhihu.log')
    zhihu_handler = RotatingFileHandler(
        zhihu_log_file,
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    zhihu_handler.setLevel(logging.DEBUG)
    zhihu_handler.setFormatter(formatter)
    qr_logger.addHandler(zhihu_handler)

    # 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    qr_logger.addHandler(console_handler)

    return qr_logger


logger = setup_qr_login_logger()


class ZhihuQRLogin:
    """知乎二维码登录类 - 基于API实现"""

    def __init__(self, cookies_dir=None):
        """
        初始化二维码登录

        Args:
            cookies_dir: Cookie存储目录
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.zhihu.com/',
            'Origin': 'https://www.zhihu.com'
        })

        self.qr_token = None
        self.xsrf_token = None

        if cookies_dir is None:
            cookies_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cookies')
        self.cookies_dir = cookies_dir
        os.makedirs(self.cookies_dir, exist_ok=True)

    def _init_session(self):
        """初始化会话，获取必要的token"""
        try:
            # 访问知乎首页获取基础cookie
            resp = self.session.get('https://www.zhihu.com/')
            if resp.status_code != 200:
                logger.error(f'访问知乎失败: {resp.status_code}')
                return False

            # 获取xsrf token
            self.xsrf_token = self.session.cookies.get('_xsrf', '')
            if not self.xsrf_token:
                logger.error('未能获取_xsrf token')
                return False

            logger.info(f'会话初始化成功，xsrf: {self.xsrf_token[:20]}...')

            # 获取udid
            udid_resp = self.session.post(
                'https://www.zhihu.com/udid',
                headers={'x-xsrftoken': self.xsrf_token}
            )
            if udid_resp.status_code == 200:
                logger.info('UDID获取成功')

            return True
        except Exception as e:
            logger.error(f'初始化会话失败: {e}', exc_info=True)
            return False

    def get_qr_code(self):
        """
        获取知乎扫码登录的二维码

        Returns:
            (success, qr_image_base64, message)
        """
        try:
            # 初始化会话
            if not self._init_session():
                return False, None, '会话初始化失败'

            # 请求二维码token
            qr_api = 'https://www.zhihu.com/api/v3/account/api/login/qrcode'
            resp = self.session.post(
                qr_api,
                headers={
                    'x-xsrftoken': self.xsrf_token,
                    'Content-Type': 'application/json'
                },
                json={}
            )

            if resp.status_code != 200:
                logger.error(f'获取二维码token失败: {resp.status_code} - {resp.text}')
                return False, None, f'获取二维码失败: {resp.status_code}'

            data = resp.json()
            self.qr_token = data.get('token')
            qr_link = data.get('link')

            if not self.qr_token or not qr_link:
                logger.error(f'二维码数据不完整: {data}')
                return False, None, '二维码数据不完整'

            logger.info(f'获取二维码token成功: {self.qr_token}')

            # 生成二维码图片
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_link)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            # 转换为base64
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

            logger.info('✓ 二维码生成成功')
            return True, qr_base64, '请使用知乎APP扫码登录'

        except Exception as e:
            logger.error(f'获取二维码失败: {e}', exc_info=True)
            return False, None, str(e)

    def check_login_status(self):
        """
        检查扫码登录状态

        Returns:
            (status_code, message, cookies)
            status_code: 0=等待扫码, 1=已扫码待确认, 2=已登录, 3=取消, 4=过期, -1=错误, -403=IP被封
        """
        if not self.qr_token:
            return -1, '无效的登录会话', None

        try:
            # 检查扫码状态
            check_api = f'https://www.zhihu.com/api/v3/account/api/login/qrcode/{self.qr_token}/scan_info'
            resp = self.session.get(
                check_api,
                headers={'x-xsrftoken': self.xsrf_token},
                timeout=10
            )

            if resp.status_code == 403:
                logger.warning(f'检查状态返回403，IP可能被封禁')
                return -403, 'IP被风控', None

            if resp.status_code != 200:
                logger.debug(f'检查状态失败: {resp.status_code}')
                return 0, '等待扫码...', None

            data = resp.json()
            status = data.get('status')

            # status: 0=等待扫码, 1=已扫码待确认, 2=已确认登录, 3=已取消, 4=已过期
            if status == 0:
                return 0, '等待扫码...', None
            elif status == 1:
                return 1, '已扫码，请在手机上确认登录', None
            elif status == 2:
                # 登录成功，获取cookie
                logger.info('✓ 扫码登录成功!')

                # 需要完成登录流程获取cookie
                login_api = f'https://www.zhihu.com/api/v3/account/api/login/qrcode/{self.qr_token}/login'
                login_resp = self.session.post(
                    login_api,
                    headers={
                        'x-xsrftoken': self.xsrf_token,
                        'Content-Type': 'application/json'
                    },
                    json={},
                    timeout=10
                )

                if login_resp.status_code == 200:
                    # 获取所有cookie
                    cookies = self.get_cookies()
                    return 2, '登录成功', cookies
                else:
                    logger.error(f'完成登录失败: {login_resp.status_code}')
                    return -1, '完成登录失败', None

            elif status == 3:
                return 3, '登录已取消', None
            elif status == 4:
                return 4, '二维码已过期，请刷新', None
            else:
                return -1, f'未知状态: {status}', None

        except Exception as e:
            logger.error(f'检查登录状态失败: {e}', exc_info=True)
            return -1, str(e), None

    def wait_for_login(self, timeout=120):
        """
        等待用户扫码登录

        Args:
            timeout: 超时时间(秒)

        Returns:
            (success, message)
        """
        try:
            start_time = time.time()

            while time.time() - start_time < timeout:
                logged_in, message, cookies = self.check_login_status()

                if logged_in:
                    return True, message

                if '过期' in message or '取消' in message:
                    return False, message

                time.sleep(2)

            return False, '登录超时'

        except Exception as e:
            logger.error(f'等待登录失败: {e}', exc_info=True)
            return False, str(e)

    def save_cookies(self, username):
        """
        保存登录后的Cookie

        Args:
            username: 用户名(用于cookie文件命名)

        Returns:
            bool: 是否保存成功
        """
        try:
            cookies = []
            for cookie in self.session.cookies:
                cookies.append({
                    'name': cookie.name,
                    'value': cookie.value,
                    'domain': cookie.domain,
                    'path': cookie.path
                })

            cookie_file = os.path.join(self.cookies_dir, f'zhihu_{username}.json')

            with open(cookie_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)

            logger.info(f'✓ Cookie已保存到: {cookie_file}')
            return True

        except Exception as e:
            logger.error(f'保存Cookie失败: {e}', exc_info=True)
            return False

    def get_cookies(self):
        """获取当前会话的cookies"""
        cookies = []
        for cookie in self.session.cookies:
            cookies.append({
                'name': cookie.name,
                'value': cookie.value,
                'domain': cookie.domain,
                'path': cookie.path
            })
        return cookies

    def get_session_data(self):
        """获取会话数据用于序列化存储"""
        cookies = []
        for cookie in self.session.cookies:
            cookies.append({
                'name': cookie.name,
                'value': cookie.value,
                'domain': cookie.domain,
                'path': cookie.path
            })
        return {
            'qr_token': self.qr_token,
            'xsrf_token': self.xsrf_token,
            'cookies': cookies
        }

    def restore_session(self, session_data):
        """从序列化数据恢复会话"""
        self.qr_token = session_data.get('qr_token')
        self.xsrf_token = session_data.get('xsrf_token')
        cookies = session_data.get('cookies', [])
        for cookie in cookies:
            self.session.cookies.set(
                cookie['name'],
                cookie['value'],
                domain=cookie.get('domain', '.zhihu.com'),
                path=cookie.get('path', '/')
            )
        logger.info(f'会话已恢复: qr_token={self.qr_token}, cookies数量={len(cookies)}')

    def complete_login(self):
        """
        完成登录流程（用于恢复会话后调用）
        多种方式尝试完成登录

        Returns:
            (success, message, cookies)
        """
        if not self.qr_token:
            return False, '无效的登录会话', None

        try:
            # 方法1: 尝试调用登录API
            login_api = f'https://www.zhihu.com/api/v3/account/api/login/qrcode/{self.qr_token}/login'
            logger.info(f'尝试方法1 - 调用登录API: {login_api}')

            login_resp = self.session.post(
                login_api,
                headers={
                    'x-xsrftoken': self.xsrf_token,
                    'Content-Type': 'application/json'
                },
                json={},
                timeout=10
            )

            logger.info(f'登录API响应: {login_resp.status_code}')

            if login_resp.status_code == 200:
                cookies = self.get_cookies()
                logger.info(f'✓ 方法1成功，获取到 {len(cookies)} 个cookie')
                return True, '登录成功', cookies

            # 方法2: 如果登录API失败，尝试访问知乎首页检查是否已登录
            logger.info('方法1失败，尝试方法2 - 访问知乎首页检查登录状态')

            home_resp = self.session.get(
                'https://www.zhihu.com/',
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                },
                timeout=10,
                allow_redirects=True
            )

            # 检查是否有z_c0 cookie（登录成功的标志）
            z_c0 = self.session.cookies.get('z_c0')
            if z_c0:
                cookies = self.get_cookies()
                logger.info(f'✓ 方法2成功，检测到z_c0 cookie，共{len(cookies)}个cookie')
                return True, '登录成功', cookies

            # 方法3: 尝试访问用户信息API
            logger.info('方法2失败，尝试方法3 - 访问用户信息API')

            me_resp = self.session.get(
                'https://www.zhihu.com/api/v4/me',
                headers={
                    'x-xsrftoken': self.xsrf_token,
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                },
                timeout=10
            )

            if me_resp.status_code == 200:
                try:
                    me_data = me_resp.json()
                    if me_data.get('id'):
                        cookies = self.get_cookies()
                        logger.info(f'✓ 方法3成功，用户已登录: {me_data.get("name", "unknown")}')
                        return True, '登录成功', cookies
                except:
                    pass

            # 所有方法都失败
            if login_resp.status_code == 403:
                logger.error(f'知乎API返回403，服务器IP被封禁')
                return False, 'IP_BLOCKED', None
            elif login_resp.status_code == 404:
                logger.warning('登录API返回404，可能用户还未在手机上确认登录')
                return False, '请在知乎APP上确认登录后重试', None
            else:
                return False, f'登录失败: {login_resp.status_code}', None

        except Exception as e:
            logger.error(f'完成登录失败: {e}', exc_info=True)
            return False, str(e), None

    def close(self):
        """关闭会话"""
        try:
            self.session.close()
            logger.info('会话已关闭')
        except Exception as e:
            logger.warning(f'关闭会话时出错: {e}')
