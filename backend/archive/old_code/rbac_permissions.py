#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RBAC权限验证模块
提供权限检查装饰器和辅助函数
"""
from functools import wraps
from flask import session, jsonify, request
from models import get_db_session, User, Role, Permission, RolePermission, Enterprise, EnterpriseMember
from sqlalchemy import text


def get_current_user():
    """获取当前登录用户"""
    user_id = session.get('user_id')
    if not user_id:
        return None

    db = get_db_session()
    try:
        user = db.query(User).filter_by(id=user_id).first()
        return user
    finally:
        db.close()


def get_user_permissions(user):
    """获取用户的所有权限代码列表"""
    if not user:
        return []

    db = get_db_session()
    try:
        permissions = set()

        # 1. 如果是系统级用户(如admin),从role_id获取权限
        if user.role_id:
            role_perms = db.query(Permission.code).join(
                RolePermission, RolePermission.permission_id == Permission.id
            ).filter(RolePermission.role_id == user.role_id).all()
            permissions.update([p[0] for p in role_perms])

        # 2. 如果是企业用户,从enterprise_members获取企业内角色权限
        if user.user_type == 'enterprise':
            enterprise_perms = db.query(Permission.code).join(
                RolePermission, RolePermission.permission_id == Permission.id
            ).join(
                EnterpriseMember, EnterpriseMember.role_id == RolePermission.role_id
            ).filter(
                EnterpriseMember.user_id == user.id,
                EnterpriseMember.status == 'active'
            ).all()
            permissions.update([p[0] for p in enterprise_perms])

        # 3. 如果是个人用户,从individual_user角色获取权限
        if user.user_type == 'individual':
            individual_role = db.query(Role).filter_by(code='individual_user').first()
            if individual_role:
                individual_perms = db.query(Permission.code).join(
                    RolePermission, RolePermission.permission_id == Permission.id
                ).filter(RolePermission.role_id == individual_role.id).all()
                permissions.update([p[0] for p in individual_perms])

        return list(permissions)
    finally:
        db.close()


def has_permission(user, resource, action):
    """检查用户是否有指定权限"""
    if not user or not user.is_active:
        return False

    # 超级管理员拥有所有权限
    if user.role_id:
        db = get_db_session()
        try:
            role = db.query(Role).filter_by(id=user.role_id).first()
            if role and role.code == 'super_admin':
                return True
        finally:
            db.close()

    # 检查用户权限列表
    permission_code = f"{resource}.{action}"
    user_permissions = get_user_permissions(user)
    return permission_code in user_permissions


def require_permission(resource, action):
    """
    权限检查装饰器
    用法: @require_permission('workflow', 'create')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()

            if not user:
                return jsonify({
                    'success': False,
                    'error': '未登录,请先登录'
                }), 401

            if not user.is_active:
                return jsonify({
                    'success': False,
                    'error': '账号已被禁用'
                }), 403

            if not has_permission(user, resource, action):
                return jsonify({
                    'success': False,
                    'error': f'权限不足,需要{resource}.{action}权限'
                }), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_enterprise_role(role_codes):
    """
    企业角色检查装饰器
    用法: @require_enterprise_role(['ENTERPRISE_OWNER', 'ENTERPRISE_ADMIN'])
    """
    if isinstance(role_codes, str):
        role_codes = [role_codes]

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()

            if not user:
                return jsonify({
                    'success': False,
                    'error': '未登录,请先登录'
                }), 401

            if not user.is_active:
                return jsonify({
                    'success': False,
                    'error': '账号已被禁用'
                }), 403

            # 从请求中获取enterprise_id
            enterprise_id = request.view_args.get('enterprise_id') or request.json.get('enterprise_id')

            if not enterprise_id:
                return jsonify({
                    'success': False,
                    'error': '缺少企业ID参数'
                }), 400

            # 检查用户在该企业的角色
            db = get_db_session()
            try:
                member = db.query(EnterpriseMember).join(
                    Role, Role.id == EnterpriseMember.role_id
                ).filter(
                    EnterpriseMember.enterprise_id == enterprise_id,
                    EnterpriseMember.user_id == user.id,
                    EnterpriseMember.status == 'active'
                ).first()

                if not member:
                    return jsonify({
                        'success': False,
                        'error': '您不是该企业成员'
                    }), 403

                role = db.query(Role).filter_by(id=member.role_id).first()

                if not role or role.code not in [code.lower() for code in role_codes]:
                    return jsonify({
                        'success': False,
                        'error': f'权限不足,需要以下角色之一: {", ".join(role_codes)}'
                    }), 403

                return f(*args, **kwargs)
            finally:
                db.close()
        return decorated_function
    return decorator


def check_resource_owner(user, resource_type, resource_id):
    """
    检查用户是否是资源的所有者

    Args:
        user: 用户对象
        resource_type: 资源类型 ('workflow', 'article', 'platform_account')
        resource_id: 资源ID

    Returns:
        bool: 是否是所有者
    """
    if not user:
        return False

    db = get_db_session()
    try:
        if resource_type == 'workflow':
            from models import Workflow
            resource = db.query(Workflow).filter_by(id=resource_id).first()
            return resource and resource.user_id == user.id

        elif resource_type == 'article':
            from models import Article, Workflow
            article = db.query(Article).join(Workflow).filter(Article.id == resource_id).first()
            return article and article.workflow.user_id == user.id

        elif resource_type == 'platform_account':
            from models import PlatformAccount
            account = db.query(PlatformAccount).filter_by(id=resource_id).first()
            return account and account.user_id == user.id

        return False
    finally:
        db.close()


def require_resource_owner(resource_type):
    """
    资源所有权检查装饰器
    用法: @require_resource_owner('workflow')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()

            if not user:
                return jsonify({
                    'success': False,
                    'error': '未登录,请先登录'
                }), 401

            # 从路径参数获取资源ID
            resource_id = kwargs.get('id') or kwargs.get(f'{resource_type}_id')

            if not resource_id:
                return jsonify({
                    'success': False,
                    'error': '缺少资源ID参数'
                }), 400

            # 超级管理员跳过所有权检查
            if user.role_id:
                db = get_db_session()
                try:
                    role = db.query(Role).filter_by(id=user.role_id).first()
                    if role and role.code == 'super_admin':
                        return f(*args, **kwargs)
                finally:
                    db.close()

            # 检查所有权
            if not check_resource_owner(user, resource_type, resource_id):
                return jsonify({
                    'success': False,
                    'error': '权限不足,您不是该资源的所有者'
                }), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def is_super_admin(user):
    """检查用户是否是超级管理员"""
    if not user or not user.role_id:
        return False

    db = get_db_session()
    try:
        role = db.query(Role).filter_by(id=user.role_id).first()
        return role and role.code == 'super_admin'
    finally:
        db.close()


def is_platform_admin(user):
    """检查用户是否是平台管理员"""
    if not user or not user.role_id:
        return False

    db = get_db_session()
    try:
        role = db.query(Role).filter_by(id=user.role_id).first()
        return role and role.code in ['super_admin', 'platform_admin']
    finally:
        db.close()


def get_user_enterprises(user):
    """获取用户所属的所有企业"""
    if not user:
        return []

    db = get_db_session()
    try:
        memberships = db.query(Enterprise, Role.code).join(
            EnterpriseMember, EnterpriseMember.enterprise_id == Enterprise.id
        ).join(
            Role, Role.id == EnterpriseMember.role_id
        ).filter(
            EnterpriseMember.user_id == user.id,
            EnterpriseMember.status == 'active'
        ).all()

        return [{
            'enterprise': enterprise.to_dict(),
            'role': role_code
        } for enterprise, role_code in memberships]
    finally:
        db.close()


def check_enterprise_member(user, enterprise_id):
    """检查用户是否是企业成员"""
    if not user or not enterprise_id:
        return False

    db = get_db_session()
    try:
        member = db.query(EnterpriseMember).filter(
            EnterpriseMember.enterprise_id == enterprise_id,
            EnterpriseMember.user_id == user.id,
            EnterpriseMember.status == 'active'
        ).first()
        return member is not None
    finally:
        db.close()
