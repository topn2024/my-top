"""
权限装饰器和认证中间件
"""
from functools import wraps
from flask import session, redirect, url_for, jsonify, request
from models import SessionLocal, User
from sqlalchemy import text

# 角色定义
ROLE_GUEST = 'guest'      # 游客（未登录）
ROLE_USER = 'user'        # 注册用户
ROLE_ADMIN = 'admin'      # 管理员

# 页面访问权限定义
PAGE_PERMISSIONS = {
    # 公开页面（所有人可访问）
    'public': [
        '/',
        '/login',
        '/register',
    ],

    # 注册用户可访问的服务页面
    'user': [
        '/platform',
        '/analysis',
        '/articles',
        '/publish',
    ],

    # 仅管理员可访问的配置页面
    'admin': [
        '/templates',
        '/template-guide',
    ]
}

def get_current_user():
    """获取当前登录用户"""
    user_id = session.get('user_id')
    if not user_id:
        return None

    db_session = SessionLocal()
    try:
        user = db_session.query(User).filter_by(id=user_id).first()
        return user
    finally:
        db_session.close()

def get_user_role():
    """获取当前用户角色"""
    user = get_current_user()
    if not user:
        return ROLE_GUEST
    return getattr(user, 'role', ROLE_USER)

def login_required(f):
    """要求用户登录的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({
                    'success': False,
                    'error': '请先登录',
                    'error_code': 'NOT_LOGGED_IN'
                }), 401
            return redirect(url_for('auth.login_page'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """要求管理员权限的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({
                    'success': False,
                    'error': '请先登录',
                    'error_code': 'NOT_LOGGED_IN'
                }), 401
            return redirect(url_for('auth.login_page'))

        role = getattr(user, 'role', 'user')
        if role != ROLE_ADMIN:
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
    """要求特定角色的装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()

            if required_role == ROLE_ADMIN:
                if not user or getattr(user, 'role', 'user') != ROLE_ADMIN:
                    if request.is_json or request.path.startswith('/api/'):
                        return jsonify({
                            'success': False,
                            'error': '需要管理员权限',
                            'error_code': 'ADMIN_REQUIRED'
                        }), 403
                    return redirect(url_for('auth.login_page'))

            elif required_role == ROLE_USER:
                if not user:
                    if request.is_json or request.path.startswith('/api/'):
                        return jsonify({
                            'success': False,
                            'error': '请先登录',
                            'error_code': 'NOT_LOGGED_IN'
                        }), 401
                    return redirect(url_for('auth.login_page'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator

def check_page_permission(path):
    """
    检查当前用户是否有权限访问指定路径
    返回: (has_permission: bool, redirect_url: str or None)
    """
    user = get_current_user()
    role = getattr(user, 'role', 'user') if user else ROLE_GUEST

    # 检查是否是公开页面
    for public_path in PAGE_PERMISSIONS['public']:
        if path == public_path or path.startswith(public_path + '/'):
            return True, None

    # 检查管理员页面
    for admin_path in PAGE_PERMISSIONS['admin']:
        if path == admin_path or path.startswith(admin_path + '/'):
            if role != ROLE_ADMIN:
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

def init_permissions(app):
    """初始化权限系统"""

    @app.before_request
    def check_permissions():
        """在每个请求前检查权限"""
        # 跳过静态文件和API请求
        if request.path.startswith('/static/') or request.path.startswith('/api/'):
            return None

        # 检查页面权限
        has_permission, redirect_url = check_page_permission(request.path)

        if not has_permission and redirect_url:
            return redirect(redirect_url)

        return None

    @app.context_processor
    def inject_user_role():
        """向模板注入用户角色信息"""
        return {
            'current_user': get_current_user(),
            'user_role': get_user_role(),
            'is_admin': get_user_role() == ROLE_ADMIN,
            'is_logged_in': get_user_role() != ROLE_GUEST
        }
