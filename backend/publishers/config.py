#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多平台发布器配置文件

包含各个平台的URL、超时时间、特定配置等
"""

# 平台配置字典
PLATFORM_CONFIG = {
    'zhihu': {
        'name': '知乎',
        'base_url': 'https://www.zhihu.com',
        'login_url': 'https://www.zhihu.com/signin',
        'write_url': 'https://zhuanlan.zhihu.com/write',
        'timeout': 30,
        'features': {
            'qrcode_login': True,
            'password_login': False,
            'markdown': True,
            'rich_text': True
        }
    },
    'csdn': {
        'name': 'CSDN',
        'base_url': 'https://www.csdn.net',
        'login_url': 'https://passport.csdn.net/login',
        'write_url': 'https://mp.csdn.net/mp_blog/creation/editor',
        'blog_url_pattern': 'https://blog.csdn.net/{username}/article/details/{article_id}',
        'timeout': 30,
        'max_tags': 3,
        'categories': [
            '移动开发', 'Web开发', '后端', '前端',
            '数据库', '运维', '云计算', '人工智能',
            '物联网', '游戏开发', '嵌入式', '其他'
        ],
        'article_types': {
            'original': '原创',
            'reprint': '转载',
            'translate': '翻译'
        },
        'features': {
            'qrcode_login': False,
            'password_login': True,
            'markdown': True,
            'rich_text': True,
            'slider_captcha': True
        }
    },
    'juejin': {
        'name': '掘金',
        'base_url': 'https://juejin.cn',
        'login_url': 'https://juejin.cn/login',
        'write_url': 'https://juejin.cn/editor/drafts/new',
        'timeout': 30,
        'max_tags': 5,
        'categories': [
            '前端', '后端', 'Android', 'iOS',
            '人工智能', '开发工具', '代码人生', '阅读'
        ],
        'features': {
            'qrcode_login': True,
            'password_login': True,
            'markdown': True,
            'rich_text': False,
            'cover_image': True
        }
    }
}


def get_platform_config(platform_name: str) -> dict:
    """
    获取指定平台的配置

    Args:
        platform_name: 平台名称

    Returns:
        平台配置字典

    Raises:
        ValueError: 不支持的平台
    """
    config = PLATFORM_CONFIG.get(platform_name.lower())
    if not config:
        raise ValueError(f'不支持的平台: {platform_name}')
    return config


def get_supported_platforms() -> list:
    """
    获取所有支持的平台列表

    Returns:
        平台名称列表
    """
    return list(PLATFORM_CONFIG.keys())


def platform_supports_feature(platform_name: str, feature: str) -> bool:
    """
    检查平台是否支持某个特性

    Args:
        platform_name: 平台名称
        feature: 特性名称

    Returns:
        是否支持该特性
    """
    try:
        config = get_platform_config(platform_name)
        return config.get('features', {}).get(feature, False)
    except ValueError:
        return False
