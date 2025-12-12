#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户认证模块
"""
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask import session, jsonify, request
from models import User, get_db_session
from datetime import datetime


def hash_password(password):
    """
    哈希密码

    Args:
        password: 明文密码

    Returns:
        密码哈希值
    """
    return generate_password_hash(password, method='pbkdf2:sha256')


def verify_password(password_hash, password):
    """
    验证密码

    Args:
        password_hash: 密码哈希值
        password: 明文密码

    Returns:
        True if password matches
    """
    return check_password_hash(password_hash, password)


def create_user(username, email, password, full_name=None):
    """
    创建新用户

    Args:
        username: 用户名
        email: 邮箱
        password: 明文密码
        full_name: 全名（可选）

    Returns:
        User 对象或 None（如果创建失败）
    """
    db = get_db_session()
    try:
        # 检查用户名是否已存在
        existing_user = db.query(User).filter_by(username=username).first()
        if existing_user:
            return None, "用户名已存在"

        # 检查邮箱是否已存在
        existing_email = db.query(User).filter_by(email=email).first()
        if existing_email:
            return None, "邮箱已被使用"

        # 创建用户
        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            full_name=full_name
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user, None

    except Exception as e:
        db.rollback()
        return None, str(e)
    finally:
        db.close()


def authenticate_user(username, password):
    """
    验证用户凭据

    Args:
        username: 用户名
        password: 明文密码

    Returns:
        User 对象或 None (分离的对象，可以安全使用)
    """
    db = get_db_session()
    try:
        user = db.query(User).filter_by(username=username, is_active=True).first()
        if user and verify_password(user.password_hash, password):
            # 更新最后登录时间
            user.last_login = datetime.now()
            db.commit()

            # 刷新以确保获取最新数据
            db.refresh(user)

            # 创建一个分离的用户对象副本
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'password_hash': user.password_hash,
                'created_at': user.created_at,
                'last_login': user.last_login,
                'is_active': user.is_active
            }

            # 使用make_transient让对象脱离session
            from sqlalchemy.orm import make_transient
            make_transient(user)

            # 恢复属性
            for key, value in user_data.items():
                setattr(user, key, value)

            return user
        return None
    except Exception as e:
        db.rollback()
        return None
    finally:
        db.close()



def get_current_user():
    """
    从 session 获取当前用户

    Returns:
        User 对象或 None
    """
    user_id = session.get('user_id')
    if not user_id:
        return None

    db = get_db_session()
    try:
        user = db.query(User).filter_by(id=user_id, is_active=True).first()
        return user
    finally:
        db.close()


def login_required(f):
    """
    装饰器：要求用户登录

    用法:
        @app.route('/api/protected')
        @login_required
        def protected_route():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({
                'success': False,
                'error': '请先登录',
                'code': 'UNAUTHORIZED'
            }), 401
        return f(*args, **kwargs)
    return decorated_function


def create_session(user):
    """
    为用户创建 session

    Args:
        user: User 对象
    """
    session['user_id'] = user.id
    session['username'] = user.username
    session.permanent = True  # 使用永久 session


def destroy_session():
    """清除当前 session"""
    session.clear()


if __name__ == '__main__':
    # 测试密码哈希
    password = "test123"
    hashed = hash_password(password)
    print(f"原密码: {password}")
    print(f"哈希值: {hashed}")
    print(f"验证成功: {verify_password(hashed, password)}")
    print(f"验证失败: {verify_password(hashed, 'wrong')}")
