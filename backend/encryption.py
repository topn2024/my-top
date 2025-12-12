#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
密码加密模块
用于加密和解密平台账号密码
"""
from cryptography.fernet import Fernet
import os
import base64


# 加密密钥 - 实际使用时应该从环境变量读取
# 生成方式: Fernet.generate_key()
ENCRYPTION_KEY = os.environ.get('TOPN_ENCRYPTION_KEY', 'TopN_Secret_Key_2024_Please_Change_This_In_Production!!')

def get_encryption_key():
    """
    获取或生成加密密钥

    Returns:
        加密密钥（bytes）
    """
    key = ENCRYPTION_KEY.encode('utf-8')
    # Fernet 需要32字节的base64编码密钥
    # 填充或截断到32字节
    key = key[:32].ljust(32, b'0')
    # 转换为base64
    return base64.urlsafe_b64encode(key)


def encrypt_password(password):
    """
    加密密码

    Args:
        password: 明文密码（str）

    Returns:
        加密后的密码（str）
    """
    if not password:
        return ''

    try:
        key = get_encryption_key()
        cipher_suite = Fernet(key)
        encrypted = cipher_suite.encrypt(password.encode('utf-8'))
        return encrypted.decode('utf-8')
    except Exception as e:
        print(f"加密失败: {e}")
        return None


def decrypt_password(encrypted_password):
    """
    解密密码

    Args:
        encrypted_password: 加密后的密码（str）

    Returns:
        明文密码（str）
    """
    if not encrypted_password:
        return ''

    try:
        key = get_encryption_key()
        cipher_suite = Fernet(key)
        decrypted = cipher_suite.decrypt(encrypted_password.encode('utf-8'))
        return decrypted.decode('utf-8')
    except Exception as e:
        print(f"解密失败: {e}")
        return None


def generate_new_key():
    """
    生成新的加密密钥

    Returns:
        新密钥（str）
    """
    key = Fernet.generate_key()
    return key.decode('utf-8')


if __name__ == '__main__':
    # 测试加密和解密
    print("=" * 60)
    print("密码加密测试")
    print("=" * 60)

    # 生成新密钥（如果需要）
    # new_key = generate_new_key()
    # print(f"\n新密钥（保存到环境变量 TOPN_ENCRYPTION_KEY）:\n{new_key}\n")

    # 测试加密解密
    test_password = "test_password_123"
    print(f"原密码: {test_password}")

    encrypted = encrypt_password(test_password)
    print(f"加密后: {encrypted}")

    decrypted = decrypt_password(encrypted)
    print(f"解密后: {decrypted}")

    if test_password == decrypted:
        print("\n✓ 加密/解密测试成功")
    else:
        print("\n✗ 加密/解密测试失败")

    print("\n" + "=" * 60)
    print("警告: 生产环境请设置环境变量 TOPN_ENCRYPTION_KEY")
    print("=" * 60)
