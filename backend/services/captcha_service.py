#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云码验证码识别服务
API文档: https://www.jfbym.com/demo.html
"""
import base64
import logging
import requests
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)


class CaptchaService:
    """云码验证码识别服务"""

    # API地址
    CUSTOM_API_URL = "http://api.jfbym.com/api/YmServer/customApi"
    FUNNEL_API_URL = "http://api.jfbym.com/api/YmServer/funnelApi"
    FUNNEL_RESULT_URL = "http://api.jfbym.com/api/YmServer/funnelApiResult"
    USER_INFO_URL = "http://api.jfbym.com/api/YmServer/getUserInfoApi"
    REFUND_URL = "http://api.jfbym.com/api/YmServer/refundApi"

    # 验证码类型 - 常用类型
    TYPE_COMMON_ALPHANUMERIC = "10110"  # 通用数英混合
    TYPE_COMMON_CHINESE = "10111"  # 通用中文
    TYPE_COMMON_ARITHMETIC = "10112"  # 通用算术
    TYPE_SLIDE_SINGLE = "20110"  # 通用单图滑块（只需背景图）
    TYPE_SLIDE_DOUBLE = "20111"  # 通用双图滑块（背景图+滑块图）- 知乎/网易易盾使用此类型
    TYPE_SLIDE_PUZZLE = "20111"  # 兼容旧代码，使用双图滑块
    TYPE_CLICK_CHINESE = "30100"  # 通用文字点选
    TYPE_CLICK_ICON = "30101"  # 通用图标点选
    TYPE_RECAPTCHA_V2 = "40010"  # 谷歌reCaptcha v2
    TYPE_RECAPTCHA_V3 = "40011"  # 谷歌reCaptcha v3

    def __init__(self, token: str = None):
        """
        初始化验证码识别服务

        Args:
            token: 云码平台的API密钥，如果不传则从配置文件读取
        """
        self.token = token
        if not self.token:
            # 尝试从配置文件读取
            try:
                import os
                import json
                config_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    'config',
                    'captcha_config.json'
                )
                if os.path.exists(config_path):
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        self.token = config.get('jfbym_token')
            except Exception as e:
                logger.warning(f'读取验证码配置失败: {e}')

        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def _image_to_base64(self, image_path: str = None, image_bytes: bytes = None) -> str:
        """
        将图片转换为base64字符串

        Args:
            image_path: 图片文件路径
            image_bytes: 图片二进制数据

        Returns:
            base64编码的字符串
        """
        if image_bytes:
            return base64.b64encode(image_bytes).decode('utf-8')
        elif image_path:
            with open(image_path, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        else:
            raise ValueError('必须提供image_path或image_bytes')

    def recognize_common(
        self,
        image_base64: str = None,
        image_path: str = None,
        image_bytes: bytes = None,
        captcha_type: str = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        识别通用类验证码（数英、中文、算术等）

        Args:
            image_base64: 图片的base64字符串
            image_path: 图片文件路径
            image_bytes: 图片二进制数据
            captcha_type: 验证码类型，默认为数英混合

        Returns:
            (success, result, response_data)
        """
        if not self.token:
            return False, '未配置云码API密钥', {}

        # 获取base64
        if image_base64:
            b64 = image_base64
        else:
            b64 = self._image_to_base64(image_path, image_bytes)

        # 默认类型
        if not captcha_type:
            captcha_type = self.TYPE_COMMON_ALPHANUMERIC

        data = {
            'token': self.token,
            'type': captcha_type,
            'image': b64
        }

        try:
            response = self.session.post(self.CUSTOM_API_URL, json=data, timeout=30)
            result = response.json()

            logger.info(f'验证码识别响应: {result}')

            if result.get('code') == 10000:
                # 识别成功
                captcha_text = result.get('data', {}).get('data', '')
                return True, captcha_text, result
            else:
                error_msg = result.get('msg', '识别失败')
                return False, error_msg, result

        except Exception as e:
            logger.error(f'验证码识别请求失败: {e}', exc_info=True)
            return False, str(e), {}

    def recognize_slide(
        self,
        slide_image_base64: str = None,
        background_image_base64: str = None,
        slide_image_bytes: bytes = None,
        background_image_bytes: bytes = None,
        captcha_type: str = None
    ) -> Tuple[bool, int, Dict[str, Any]]:
        """
        识别滑块验证码（双图滑块，适用于知乎/网易易盾等）

        云码滑块类型说明：
        - 20110: 通用单图滑块（只需背景图，自动识别缺口位置）
        - 20111: 通用双图滑块（需要背景图+滑块图）- 知乎/网易易盾使用此类型

        Args:
            slide_image_base64: 滑块小图的base64
            background_image_base64: 背景大图的base64
            slide_image_bytes: 滑块小图二进制
            background_image_bytes: 背景大图二进制
            captcha_type: 验证码类型，默认使用20111（双图滑块）

        Returns:
            (success, distance, response_data) - distance为滑动距离（像素）
        """
        if not self.token:
            return False, 0, {'error': '未配置云码API密钥'}

        # 获取base64
        if slide_image_base64:
            slide_b64 = slide_image_base64
        else:
            slide_b64 = self._image_to_base64(image_bytes=slide_image_bytes)

        if background_image_base64:
            bg_b64 = background_image_base64
        else:
            bg_b64 = self._image_to_base64(image_bytes=background_image_bytes)

        # 默认使用双图滑块类型（20111），适用于知乎/网易易盾
        if not captcha_type:
            captcha_type = self.TYPE_SLIDE_DOUBLE

        # 云码API要求的参数名
        data = {
            'token': self.token,
            'type': captcha_type,
            'slide_image': slide_b64,
            'background_image': bg_b64
        }

        try:
            logger.info(f'调用云码滑块识别API，类型: {captcha_type}')
            response = self.session.post(self.CUSTOM_API_URL, json=data, timeout=30)
            result = response.json()

            logger.info(f'滑块验证码识别响应: code={result.get("code")}, msg={result.get("msg")}')

            if result.get('code') == 10000:
                distance = int(result.get('data', {}).get('data', 0))
                logger.info(f'✓ 滑块识别成功，滑动距离: {distance}px')
                return True, distance, result
            else:
                error_msg = result.get('msg', '识别失败')
                logger.warning(f'滑块识别失败: {error_msg}')
                return False, 0, {'error': error_msg, 'response': result}

        except Exception as e:
            logger.error(f'滑块验证码识别请求失败: {e}', exc_info=True)
            return False, 0, {'error': str(e)}

    def recognize_click(
        self,
        image_base64: str = None,
        image_bytes: bytes = None,
        extra: str = '',
        captcha_type: str = None
    ) -> Tuple[bool, list, Dict[str, Any]]:
        """
        识别点选类验证码

        Args:
            image_base64: 图片的base64
            image_bytes: 图片二进制
            extra: 需要按语义点选的文字（如"请依次点击：春夏秋冬"中的"春夏秋冬"）
            captcha_type: 验证码类型

        Returns:
            (success, coordinates, response_data) - coordinates为坐标列表 [(x1,y1), (x2,y2), ...]
        """
        if not self.token:
            return False, [], {'error': '未配置云码API密钥'}

        if image_base64:
            b64 = image_base64
        else:
            b64 = self._image_to_base64(image_bytes=image_bytes)

        if not captcha_type:
            captcha_type = self.TYPE_CLICK_CHINESE

        data = {
            'token': self.token,
            'type': captcha_type,
            'image': b64,
            'extra': extra
        }

        try:
            response = self.session.post(self.CUSTOM_API_URL, json=data, timeout=30)
            result = response.json()

            logger.info(f'点选验证码识别响应: {result}')

            if result.get('code') == 10000:
                # 解析坐标，格式通常是 "x1,y1|x2,y2|x3,y3"
                coords_str = result.get('data', {}).get('data', '')
                coordinates = []
                if coords_str:
                    for coord in coords_str.split('|'):
                        parts = coord.split(',')
                        if len(parts) == 2:
                            coordinates.append((int(parts[0]), int(parts[1])))
                return True, coordinates, result
            else:
                error_msg = result.get('msg', '识别失败')
                return False, [], {'error': error_msg, 'response': result}

        except Exception as e:
            logger.error(f'点选验证码识别请求失败: {e}', exc_info=True)
            return False, [], {'error': str(e)}

    def get_balance(self) -> Tuple[bool, float, Dict[str, Any]]:
        """
        获取账户余额

        Returns:
            (success, balance, response_data)
        """
        if not self.token:
            return False, 0, {'error': '未配置云码API密钥'}

        data = {
            'token': self.token,
            'type': 'score'
        }

        try:
            response = self.session.post(self.USER_INFO_URL, json=data, timeout=10)
            result = response.json()

            if result.get('code') == 10001:
                balance = float(result.get('data', {}).get('score', 0))
                return True, balance, result
            else:
                return False, 0, result

        except Exception as e:
            logger.error(f'获取余额失败: {e}', exc_info=True)
            return False, 0, {'error': str(e)}

    def report_error(self, unique_code: str) -> Tuple[bool, str]:
        """
        报错退分（识别结果错误时调用）

        Args:
            unique_code: 识别结果返回的uniqueCode

        Returns:
            (success, message)
        """
        if not self.token:
            return False, '未配置云码API密钥'

        data = {
            'token': self.token,
            'uniqueCode': unique_code
        }

        try:
            response = self.session.post(self.REFUND_URL, json=data, timeout=10)
            result = response.json()

            if result.get('code') == 200:
                return True, result.get('msg', '退分成功')
            else:
                return False, result.get('msg', '退分失败')

        except Exception as e:
            logger.error(f'报错退分失败: {e}', exc_info=True)
            return False, str(e)


# 便捷函数
def recognize_captcha(
    image_base64: str = None,
    image_bytes: bytes = None,
    captcha_type: str = None,
    token: str = None
) -> Tuple[bool, str]:
    """
    快捷识别验证码

    Args:
        image_base64: 图片base64
        image_bytes: 图片二进制
        captcha_type: 验证码类型
        token: API密钥

    Returns:
        (success, result_or_error)
    """
    service = CaptchaService(token=token)
    success, result, _ = service.recognize_common(
        image_base64=image_base64,
        image_bytes=image_bytes,
        captcha_type=captcha_type
    )
    return success, result


if __name__ == '__main__':
    # 测试代码
    import sys

    if len(sys.argv) > 1:
        token = sys.argv[1]
        service = CaptchaService(token=token)

        # 测试获取余额
        success, balance, data = service.get_balance()
        if success:
            print(f'账户余额: {balance}')
        else:
            print(f'获取余额失败: {data}')
