#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一的认证和权限管理模块
整合了 auth.py 和 auth_decorators.py 的功能
"""
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask import session, jsonify, request, redirect, url_for
from models_unified import User, get_db_session
from datetime import datetime


# ============================================================================
# 角色定义
# ============================================================================

ROLE_GUEST = 'guest'        # 游客（未登录）
ROLE_USER = 'user'          # 注册用户
ROLE_ADMIN = 'admin'        # 管理员

# 管理员识别列表
ADMIN_USERNAMES = ['admin', 'administrator', 'superuser', 'root']
ADMIN_ROLES = ['admin', 'administrator', 'superuser', 'root']


# ============================================================================
# 密码管理
# ============================================================================

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


# ============================================================================
# 用户管理
# ============================================================================

def create_user(username, email, password, full_name=None, role='user'):
    """
    创建新用户

    Args:
        username: 用户名
        email: 邮箱
        password: 明文密码
        full_name: 全名（可选）
        role: 用户角色（默认为 'user'）

    Returns:
        (User 对象, None) 或 (None, 错误消息)
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
            full_name=full_name,
            role=role
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # 获取用户信息（分离对象）
        user_id = user.id
        user_username = user.username
        user_email = user.email
        user_role = user.role

        db.close()

        # 返回分离的用户对象
        result_user = User()
        result_user.id = user_id
        result_user.username = user_username
        result_user.email = user_email
        result_user.role = user_role

        return result_user, None

    except Exception as e:
        db.rollback()
        db.close()
        return None, str(e)


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
            db.refresh(user)

            # 创建分离的用户对象副本
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role,
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
        if user:
            # 创建分离对象以避免session问题
            user_data = user.to_dict()
            detached_user = User()
            for key, value in user_data.items():
                if hasattr(detached_user, key):
                    setattr(detached_user, key, value)
            return detached_user
        return None
    finally:
        db.close()


def get_user_role(user=None):
    """
    获取用户角色

    Args:
        user: User对象（可选，不提供则获取当前用户）

    Returns:
        角色字符串
    """
    if user is None:
        user = get_current_user()

    if not user:
        return ROLE_GUEST

    return getattr(user, 'role', ROLE_USER)


def is_admin(user=None):
    """
    检查用户是否为管理员

    Args:
        user: User对象（可选，不提供则检查当前用户）

    Returns:
        True if user is admin
    """
    if user is None:
        user = get_current_user()

    if not user:
        return False

    role = getattr(user, 'role', 'user')
    username = getattr(user, 'username', '').lower()

    # 管理员判断条件：
    # 1. role 字段为 admin 或其他管理员角色
    # 2. 用户名为管理员用户名
    return (
        role in ADMIN_ROLES or
        username in ADMIN_USERNAMES
    )


# ============================================================================
# Session 管理
# ============================================================================

def create_session(user):
    """
    为用户创建 session

    Args:
        user: User 对象
    """
    session['user_id'] = user.id
    session['username'] = user.username
    session['role'] = getattr(user, 'role', ROLE_USER)
    session.permanent = True  # 使用永久 session


def destroy_session():
    """清除当前 session"""
    session.clear()


# ============================================================================
# 装饰器
# ============================================================================

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
            # 判断是API请求还是页面请求
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({
                    'success': False,
                    'error': '请先登录',
                    'error_code': 'NOT_LOGGED_IN'
                }), 401
            # 页面请求重定向到登录页
            return redirect(url_for('auth.login_page', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """
    装饰器：要求管理员权限

    用法:
        @app.route('/api/admin/users')
        @admin_required
        def admin_route():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()

        # 检查是否登录
        if not user:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({
                    'success': False,
                    'error': '请先登录',
                    'error_code': 'NOT_LOGGED_IN'
                }), 401
            return redirect(url_for('auth.login_page', next=request.url))

        # 检查是否为管理员
        if not is_admin(user):
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({
                    'success': False,
                    'error': '需要管理员权限',
                    'error_code': 'ADMIN_REQUIRED'
                }), 403
            return jsonify({
                'success': False,
                'error': '需要管理员权限访问此页面'
            }), 403

        return f(*args, **kwargs)
    return decorated_function


def role_required(required_role):
    """
    装饰器：要求特定角色

    用法:
        @app.route('/api/special')
        @role_required('admin')
        def special_route():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()

            # 检查是否登录
            if not user:
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({
                        'success': False,
                        'error': '请先登录',
                        'error_code': 'NOT_LOGGED_IN'
                    }), 401
                return redirect(url_for('auth.login_page', next=request.url))

            # 检查角色
            user_role = get_user_role(user)

            if required_role == ROLE_ADMIN:
                if not is_admin(user):
                    if request.is_json or request.path.startswith('/api/'):
                        return jsonify({
                            'success': False,
                            'error': '需要管理员权限',
                            'error_code': 'ADMIN_REQUIRED'
                        }), 403
                    return redirect(url_for('auth.login_page'))
            elif user_role != required_role:
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({
                        'success': False,
                        'error': f'需要 {required_role} 角色权限',
                        'error_code': 'ROLE_REQUIRED'
                    }), 403
                return redirect(url_for('auth.login_page'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ============================================================================
# 页面权限配置
# ============================================================================

PAGE_PERMISSIONS = {
    # 公开页面（所有人可访问）
    'public': [
        '/',
        '/login',
        '/register',
        '/help',
    ],

    # 注册用户可访问的服务页面
    'user': [
        '/home',
        '/platform',
        '/analysis',
        '/articles',
        '/publish',
        '/input',
    ],

    # 仅管理员可访问的配置页面
    'admin': [
        '/admin',
        '/templates',
        '/template-guide',
        '/prompt-management',
    ]
}


def check_page_permission(path):
    """
    检查当前用户是否有权限访问指定路径

    Returns:
        (has_permission: bool, redirect_url: str or None)
    """
    user = get_current_user()
    role = get_user_role(user)

    # 检查是否是公开页面
    for public_path in PAGE_PERMISSIONS['public']:
        if path == public_path or path.startswith(public_path + '/'):
            return True, None

    # 检查管理员页面
    for admin_path in PAGE_PERMISSIONS['admin']:
        if path == admin_path or path.startswith(admin_path + '/'):
            if not is_admin(user):
                return False, '/login'
            return True, None

    # 检查用户页面
    for user_path in PAGE_PERMISSIONS['user']:
        if path == user_path or path.startswith(user_path + '/'):
            if role == ROLE_GUEST:
                return False, '/login'
            return True, None

    # 默认：公开访问
    return True, None


def init_auth(app):
    """
    初始化认证系统

    Args:
        app: Flask应用实例
    """

    @app.before_request
    def check_permissions():
        """在每个请求前检查权限"""
        # 跳过静态文件和API请求（API由装饰器控制）
        if request.path.startswith('/static/') or request.path.startswith('/api/'):
            return None

        # 检查页面权限
        has_permission, redirect_url = check_page_permission(request.path)

        if not has_permission and redirect_url:
            return redirect(redirect_url)

        return None

    @app.context_processor
    def inject_user_context():
        """向模板注入用户上下文"""
        user = get_current_user()
        return {
            'current_user': user,
            'user_role': get_user_role(user),
            'is_admin': is_admin(user),
            'is_logged_in': user is not None
        }


# ============================================================================
# 向后兼容性导出
# ============================================================================

# 为了保持与现有代码的兼容性，导出常用函数
__all__ = [
    # 角色常量
    'ROLE_GUEST', 'ROLE_USER', 'ROLE_ADMIN',
    # 密码管理
    'hash_password', 'verify_password',
    # 用户管理
    'create_user', 'authenticate_user', 'get_current_user', 'get_user_role', 'is_admin',
    # Session管理
    'create_session', 'destroy_session',
    # 装饰器
    'login_required', 'admin_required', 'role_required',
    # 权限检查
    'check_page_permission', 'init_auth',
    # 页面权限配置
    'PAGE_PERMISSIONS',
]


if __name__ == '__main__':
    # 测试密码哈希
    password = "test123"
    hashed = hash_password(password)
    print(f"原密码: {password}")
    print(f"哈希值: {hashed}")
    print(f"验证成功: {verify_password(hashed, password)}")
    print(f"验证失败: {verify_password(hashed, 'wrong')}")

    # 测试角色检查
    print(f"\n角色常量:")
    print(f"ROLE_GUEST = {ROLE_GUEST}")
    print(f"ROLE_USER = {ROLE_USER}")
    print(f"ROLE_ADMIN = {ROLE_ADMIN}")
