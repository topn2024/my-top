"""
认证路由蓝图
处理用户注册、登录、登出
"""
from flask import Blueprint, request, jsonify, session
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth import create_user, authenticate_user
from auth_decorators import login_required
from logger_config import setup_logger, log_api_request

logger = setup_logger(__name__)

# 创建蓝图
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
@log_api_request("用户注册")
def register():
    """用户注册"""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        email = data.get('email', '')
        full_name = data.get('full_name')

        if not username or not password:
            return jsonify({'error': '用户名和密码不能为空'}), 400

        if not email:
            return jsonify({'error': '邮箱不能为空'}), 400

        # 创建用户 - 注意参数顺序
        user, error = create_user(username, email, password, full_name)

        if user:
            logger.info(f'User registered: {username}')
            return jsonify({
                'success': True,
                'message': '注册成功',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            })
        else:
            return jsonify({'error': error or '注册失败'}), 400

    except Exception as e:
        logger.error(f'Registration failed: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
@log_api_request("用户登录")
def login():
    """用户登录"""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': '用户名和密码不能为空'}), 400

        # 认证用户
        user = authenticate_user(username, password)

        if user:
            # 设置session
            session['user_id'] = user.id
            session.permanent = True

            logger.info(f'User logged in: {username}')
            return jsonify({
                'success': True,
                'message': '登录成功',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            })
        else:
            return jsonify({'error': '用户名或密码错误'}), 401

    except Exception as e:
        logger.error(f'Login failed: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """用户登出"""
    try:
        user = get_current_user()
        username = user.username if user else 'unknown'

        session.pop('user_id', None)

        logger.info(f'User logged out: {username}')
        return jsonify({
            'success': True,
            'message': '登出成功'
        })

    except Exception as e:
        logger.error(f'Logout failed: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/me', methods=['GET'])
@login_required
@log_api_request("获取当前用户信息")
def get_current_user_info():
    """获取当前用户信息"""
    try:
        from auth_decorators import get_current_user as get_user_with_role
        user = get_user_with_role()

        if user:
            role = getattr(user, 'role', 'user')
            return jsonify({
                'success': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': role,
                    'created_at': user.created_at.isoformat() if hasattr(user, 'created_at') else None
                }
            })
        else:
            return jsonify({'success': False, 'error': '未登录'}), 401

    except Exception as e:
        logger.error(f'Get current user failed: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
