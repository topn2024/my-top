#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSDN微信扫码登录模块
类似知乎二维码登录方案,提取微信扫码二维码发送给前端
"""
import time
import os
import base64
import logging
from DrissionPage import ChromiumPage, ChromiumOptions
from flask import Blueprint, request, jsonify
from models import get_db_session, PlatformAccount
from auth import login_required, get_current_user
import json

logger = logging.getLogger(__name__)

csdn_wechat_bp = Blueprint('csdn_wechat', __name__)

# 全局变量存储登录会话
_login_sessions = {}

class CSDNWechatLogin:
    """CSDN微信扫码登录类"""

    def __init__(self):
        self.driver = None
        self.qr_image_path = None
        self.login_url = 'https://passport.csdn.net/login'
        self.cookies_dir = os.path.join(os.path.dirname(__file__), 'cookies')
        os.makedirs(self.cookies_dir, exist_ok=True)

    def init_browser(self):
        """初始化浏览器"""
        try:
            co = ChromiumOptions()
            co.set_argument('--disable-blink-features=AutomationControlled')
            co.set_argument('--start-maximized')
            co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

            self.driver = ChromiumPage(addr_or_opts=co)
            logger.info('CSDN登录浏览器初始化成功')
            return True
        except Exception as e:
            logger.error(f'浏览器初始化失败: {e}')
            return False

    def get_wechat_qr_code(self):
        """
        获取CSDN微信扫码登录的二维码

        Returns:
            (success, qr_image_base64, message)
        """
        try:
            if not self.driver:
                if not self.init_browser():
                    return False, None, '浏览器初始化失败'

            # 访问登录页面
            logger.info('访问CSDN登录页面...')
            self.driver.get(self.login_url)
            time.sleep(2)

            # 查找并点击微信登录按钮
            try:
                # 尝试多种选择器定位微信登录按钮
                wechat_btn = None
                selectors = [
                    'text:微信登录',
                    'text:微信',
                    '.wechat-login',
                    '@@title=微信登录',
                    'img[alt*="微信"]',
                ]

                for selector in selectors:
                    try:
                        wechat_btn = self.driver.ele(selector, timeout=2)
                        if wechat_btn:
                            logger.info(f'找到微信登录按钮: {selector}')
                            break
                    except:
                        continue

                if wechat_btn:
                    wechat_btn.click()
                    logger.info('已点击微信登录按钮')
                    time.sleep(2)
                else:
                    logger.warning('未找到微信登录按钮,尝试直接查找二维码')
            except Exception as e:
                logger.warning(f'点击微信登录按钮失败: {e}')

            # 查找二维码图片
            qr_img = None
            qr_selectors = [
                'tag:img@@alt=微信扫码',
                '.qrcode img',
                '.login-qr img',
                'tag:img@@src*=qrcode',
                '#qrcode img',
                '.wechat-qr img',
            ]

            for selector in qr_selectors:
                try:
                    qr_img = self.driver.ele(selector, timeout=2)
                    if qr_img:
                        logger.info(f'找到二维码图片: {selector}')
                        break
                except:
                    continue

            if not qr_img:
                # 尝试截取整个页面中的二维码区域
                logger.warning('未找到二维码图片元素,尝试截屏')
                screenshot_path = os.path.join(self.cookies_dir, 'csdn_qr_temp.png')
                self.driver.get_screenshot(screenshot_path)

                with open(screenshot_path, 'rb') as f:
                    qr_image_base64 = base64.b64encode(f.read()).decode('utf-8')

                return True, qr_image_base64, '请扫描二维码登录(整页截图)'

            # 获取二维码图片
            # 方法1: 从src属性获取base64
            src = qr_img.attr('src')
            if src and src.startswith('data:image'):
                # data:image/png;base64,xxxx
                qr_image_base64 = src.split(',')[1]
                logger.info('从src获取到base64二维码')
                return True, qr_image_base64, '请使用微信扫描二维码'

            # 方法2: 截图二维码元素
            try:
                qr_path = os.path.join(self.cookies_dir, 'csdn_wechat_qr.png')
                qr_img.get_screenshot(qr_path)

                with open(qr_path, 'rb') as f:
                    qr_image_base64 = base64.b64encode(f.read()).decode('utf-8')

                logger.info('通过截图获取到二维码')
                return True, qr_image_base64, '请使用微信扫描二维码'
            except Exception as e:
                logger.error(f'截图二维码失败: {e}')
                return False, None, '获取二维码失败'

        except Exception as e:
            logger.error(f'获取微信二维码失败: {e}', exc_info=True)
            return False, None, f'获取二维码失败: {str(e)}'

    def check_login_status(self, max_wait=300):
        """
        检查登录状态(轮询)

        Args:
            max_wait: 最大等待时间(秒)

        Returns:
            (success, message)
        """
        try:
            start_time = time.time()

            while time.time() - start_time < max_wait:
                # 检查是否已登录
                # 方法1: 检查URL变化
                current_url = self.driver.url
                if current_url != self.login_url and 'login' not in current_url:
                    logger.info(f'检测到URL变化: {current_url}')
                    time.sleep(2)  # 等待页面完全加载

                    # 验证是否真的登录成功
                    if self.is_logged_in():
                        logger.info('微信扫码登录成功')
                        return True, '登录成功'

                # 方法2: 检查页面元素
                try:
                    # 查找登录成功的标志(用户头像/用户名等)
                    success_indicators = [
                        '.user-info',
                        '.user-avatar',
                        '.username',
                        'text:退出登录',
                    ]

                    for indicator in success_indicators:
                        try:
                            elem = self.driver.ele(indicator, timeout=1)
                            if elem:
                                logger.info(f'检测到登录成功标志: {indicator}')
                                return True, '登录成功'
                        except:
                            continue
                except:
                    pass

                # 方法3: 检查二维码是否过期
                try:
                    expired_elem = self.driver.ele('text:二维码已过期', timeout=1)
                    if expired_elem:
                        logger.warning('二维码已过期')
                        return False, '二维码已过期,请重新获取'
                except:
                    pass

                time.sleep(1)  # 每秒检查一次

            logger.warning('登录超时')
            return False, '登录超时,请重试'

        except Exception as e:
            logger.error(f'检查登录状态失败: {e}')
            return False, f'检查登录失败: {str(e)}'

    def is_logged_in(self):
        """验证是否已登录"""
        try:
            # 访问CSDN首页检查登录状态
            self.driver.get('https://www.csdn.net')
            time.sleep(2)

            # 检查Cookie
            cookies = self.driver.cookies(as_dict=True)
            if 'UserToken' in cookies or 'uuid_tt_dd' in cookies:
                logger.info('检测到登录Cookie')
                return True

            # 检查页面元素
            user_elem = self.driver.ele('.toolbar-menu-item user', timeout=2)
            if user_elem:
                logger.info('检测到用户元素')
                return True

            return False
        except:
            return False

    def save_cookies(self, username):
        """
        保存Cookie

        Args:
            username: CSDN用户名(用于标识Cookie文件)

        Returns:
            (success, cookie_file_path)
        """
        try:
            cookies = self.driver.cookies(as_dict=False)

            cookie_file = os.path.join(self.cookies_dir, f'csdn_{username}.json')
            with open(cookie_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)

            logger.info(f'Cookie已保存: {cookie_file}')
            return True, cookie_file
        except Exception as e:
            logger.error(f'保存Cookie失败: {e}')
            return False, None

    def close(self):
        """关闭浏览器"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info('浏览器已关闭')
            except:
                pass

@csdn_wechat_bp.route('/api/csdn/wechat_qr', methods=['POST'])
@login_required
def get_csdn_wechat_qr():
    """获取CSDN微信扫码登录二维码"""
    try:
        user = get_current_user()
        data = request.json
        username = data.get('username', '')  # CSDN用户名,用于保存Cookie

        if not username:
            return jsonify({
                'success': False,
                'message': '请提供CSDN用户名'
            }), 400

        # 创建登录会话
        session_id = f"{user.id}_{username}_{int(time.time())}"
        login_session = CSDNWechatLogin()

        # 获取二维码
        success, qr_base64, message = login_session.get_wechat_qr_code()

        if not success:
            login_session.close()
            return jsonify({
                'success': False,
                'message': message
            }), 400

        # 保存会话
        _login_sessions[session_id] = {
            'login': login_session,
            'username': username,
            'user_id': user.id,
            'created_at': time.time()
        }

        logger.info(f'已创建CSDN微信登录会话: {session_id}')

        return jsonify({
            'success': True,
            'session_id': session_id,
            'qr_image': f'data:image/png;base64,{qr_base64}',
            'message': message
        })

    except Exception as e:
        logger.error(f'Get CSDN wechat QR failed: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取二维码失败: {str(e)}'
        }), 500

@csdn_wechat_bp.route('/api/csdn/wechat_login_status', methods=['POST'])
@login_required
def check_csdn_wechat_login_status():
    """检查CSDN微信扫码登录状态"""
    try:
        user = get_current_user()
        data = request.json
        session_id = data.get('session_id')

        if not session_id or session_id not in _login_sessions:
            return jsonify({
                'success': False,
                'logged_in': False,
                'message': '无效的会话ID'
            }), 400

        session_data = _login_sessions[session_id]
        login_session = session_data['login']
        username = session_data['username']

        # 检查登录状态(不阻塞,快速检查)
        success, message = login_session.check_login_status(max_wait=2)

        if success:
            # 登录成功,保存Cookie
            cookie_success, cookie_file = login_session.save_cookies(username)

            if cookie_success:
                # 更新数据库
                db = get_db_session()
                try:
                    account = db.query(PlatformAccount).filter_by(
                        user_id=user.id,
                        platform='CSDN',
                        username=username
                    ).first()

                    if account:
                        account.status = 'success'
                        account.notes = '微信扫码登录成功'
                        db.commit()
                except:
                    db.rollback()
                finally:
                    db.close()

            # 清理会话
            login_session.close()
            del _login_sessions[session_id]

            logger.info(f'CSDN微信登录成功: {username}')

            return jsonify({
                'success': True,
                'logged_in': True,
                'message': '登录成功,Cookie已保存'
            })
        else:
            # 还未登录或登录失败
            return jsonify({
                'success': True,
                'logged_in': False,
                'message': message
            })

    except Exception as e:
        logger.error(f'Check CSDN wechat login status failed: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'logged_in': False,
            'message': f'检查登录状态失败: {str(e)}'
        }), 500

@csdn_wechat_bp.route('/api/csdn/cancel_wechat_login', methods=['POST'])
@login_required
def cancel_csdn_wechat_login():
    """取消CSDN微信扫码登录"""
    try:
        data = request.json
        session_id = data.get('session_id')

        if session_id and session_id in _login_sessions:
            session_data = _login_sessions[session_id]
            session_data['login'].close()
            del _login_sessions[session_id]
            logger.info(f'已取消CSDN微信登录会话: {session_id}')

        return jsonify({
            'success': True,
            'message': '已取消登录'
        })

    except Exception as e:
        logger.error(f'Cancel CSDN wechat login failed: {e}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 清理过期会话(定时任务)
def cleanup_expired_sessions():
    """清理超过30分钟的过期会话"""
    try:
        current_time = time.time()
        expired_sessions = []

        for session_id, session_data in _login_sessions.items():
            if current_time - session_data['created_at'] > 1800:  # 30分钟
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            try:
                _login_sessions[session_id]['login'].close()
                del _login_sessions[session_id]
                logger.info(f'已清理过期会话: {session_id}')
            except:
                pass

    except Exception as e:
        logger.error(f'清理过期会话失败: {e}')
