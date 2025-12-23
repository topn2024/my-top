#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业管理API模块
提供企业CRUD、成员管理、邀请系统等接口
"""
from flask import Blueprint, request, jsonify, session
from models import (
    get_db_session, Enterprise, User, Role, EnterpriseMember,
    Workflow, Permission, RolePermission
)
from rbac_permissions import (
    get_current_user, require_permission, require_enterprise_role,
    is_super_admin, is_platform_admin
)
from sqlalchemy import text
import secrets
import string

# 创建蓝图
enterprise_bp = Blueprint('enterprise', __name__, url_prefix='/api/enterprises')


# ==================== 企业CRUD接口 ====================

@enterprise_bp.route('', methods=['POST'])
@require_permission('enterprise', 'create')
def create_enterprise():
    """创建企业"""
    user = get_current_user()
    data = request.json

    if not data.get('name') or not data.get('code'):
        return jsonify({
            'success': False,
            'error': '企业名称和标识码不能为空'
        }), 400

    db = get_db_session()
    try:
        # 检查企业标识码是否已存在
        existing = db.query(Enterprise).filter_by(code=data['code']).first()
        if existing:
            return jsonify({
                'success': False,
                'error': '企业标识码已存在'
            }), 400

        # 创建企业
        enterprise = Enterprise(
            name=data['name'],
            code=data['code'],
            industry=data.get('industry'),
            description=data.get('description'),
            logo_url=data.get('logo_url'),
            contact_email=data.get('contact_email'),
            contact_phone=data.get('contact_phone'),
            max_members=data.get('max_members', 10),
            subscription_plan=data.get('subscription_plan', 'free')
        )
        db.add(enterprise)
        db.flush()

        # 将创建者设为企业所有者
        owner_role = db.query(Role).filter_by(code='enterprise_owner').first()
        if owner_role:
            member = EnterpriseMember(
                enterprise_id=enterprise.id,
                user_id=user.id,
                role_id=owner_role.id,
                status='active'
            )
            db.add(member)

        # 更新用户类型为企业用户
        if user.user_type == 'individual':
            user.user_type = 'enterprise'

        db.commit()

        return jsonify({
            'success': True,
            'message': '企业创建成功',
            'enterprise': enterprise.to_dict()
        })

    except Exception as e:
        db.rollback()
        return jsonify({
            'success': False,
            'error': f'创建企业失败: {str(e)}'
        }), 500
    finally:
        db.close()


@enterprise_bp.route('', methods=['GET'])
def list_enterprises():
    """获取企业列表"""
    user = get_current_user()

    if not user:
        return jsonify({
            'success': False,
            'error': '未登录'
        }), 401

    db = get_db_session()
    try:
        # 如果是平台管理员,返回所有企业
        if is_platform_admin(user):
            enterprises = db.query(Enterprise).all()
        else:
            # 普通用户只能看到自己所属的企业
            enterprises = db.query(Enterprise).join(
                EnterpriseMember, EnterpriseMember.enterprise_id == Enterprise.id
            ).filter(
                EnterpriseMember.user_id == user.id,
                EnterpriseMember.status == 'active'
            ).all()

        return jsonify({
            'success': True,
            'enterprises': [e.to_dict() for e in enterprises],
            'count': len(enterprises)
        })

    finally:
        db.close()


@enterprise_bp.route('/<int:enterprise_id>', methods=['GET'])
def get_enterprise(enterprise_id):
    """获取企业详情"""
    user = get_current_user()

    if not user:
        return jsonify({
            'success': False,
            'error': '未登录'
        }), 401

    db = get_db_session()
    try:
        enterprise = db.query(Enterprise).filter_by(id=enterprise_id).first()

        if not enterprise:
            return jsonify({
                'success': False,
                'error': '企业不存在'
            }), 404

        # 检查权限(平台管理员或企业成员)
        if not is_platform_admin(user):
            member = db.query(EnterpriseMember).filter(
                EnterpriseMember.enterprise_id == enterprise_id,
                EnterpriseMember.user_id == user.id,
                EnterpriseMember.status == 'active'
            ).first()

            if not member:
                return jsonify({
                    'success': False,
                    'error': '无权访问该企业'
                }), 403

        # 获取成员统计
        member_count = db.query(EnterpriseMember).filter(
            EnterpriseMember.enterprise_id == enterprise_id,
            EnterpriseMember.status == 'active'
        ).count()

        result = enterprise.to_dict()
        result['member_count'] = member_count

        return jsonify({
            'success': True,
            'enterprise': result
        })

    finally:
        db.close()


@enterprise_bp.route('/<int:enterprise_id>', methods=['PUT'])
@require_enterprise_role(['enterprise_owner', 'enterprise_admin'])
def update_enterprise(enterprise_id):
    """更新企业信息"""
    data = request.json

    db = get_db_session()
    try:
        enterprise = db.query(Enterprise).filter_by(id=enterprise_id).first()

        if not enterprise:
            return jsonify({
                'success': False,
                'error': '企业不存在'
            }), 404

        # 更新字段
        if 'name' in data:
            enterprise.name = data['name']
        if 'industry' in data:
            enterprise.industry = data['industry']
        if 'description' in data:
            enterprise.description = data['description']
        if 'logo_url' in data:
            enterprise.logo_url = data['logo_url']
        if 'contact_email' in data:
            enterprise.contact_email = data['contact_email']
        if 'contact_phone' in data:
            enterprise.contact_phone = data['contact_phone']

        db.commit()

        return jsonify({
            'success': True,
            'message': '企业信息更新成功',
            'enterprise': enterprise.to_dict()
        })

    except Exception as e:
        db.rollback()
        return jsonify({
            'success': False,
            'error': f'更新失败: {str(e)}'
        }), 500
    finally:
        db.close()


@enterprise_bp.route('/<int:enterprise_id>', methods=['DELETE'])
@require_enterprise_role(['enterprise_owner'])
def delete_enterprise(enterprise_id):
    """删除企业(仅所有者)"""
    db = get_db_session()
    try:
        enterprise = db.query(Enterprise).filter_by(id=enterprise_id).first()

        if not enterprise:
            return jsonify({
                'success': False,
                'error': '企业不存在'
            }), 404

        # 删除企业(级联删除成员和关联数据)
        db.delete(enterprise)
        db.commit()

        return jsonify({
            'success': True,
            'message': '企业已删除'
        })

    except Exception as e:
        db.rollback()
        return jsonify({
            'success': False,
            'error': f'删除失败: {str(e)}'
        }), 500
    finally:
        db.close()


# ==================== 成员管理接口 ====================

@enterprise_bp.route('/<int:enterprise_id>/members', methods=['GET'])
def list_members(enterprise_id):
    """获取企业成员列表"""
    user = get_current_user()

    if not user:
        return jsonify({
            'success': False,
            'error': '未登录'
        }), 401

    db = get_db_session()
    try:
        # 检查是否是企业成员
        if not is_platform_admin(user):
            member = db.query(EnterpriseMember).filter(
                EnterpriseMember.enterprise_id == enterprise_id,
                EnterpriseMember.user_id == user.id,
                EnterpriseMember.status == 'active'
            ).first()

            if not member:
                return jsonify({
                    'success': False,
                    'error': '无权访问该企业'
                }), 403

        # 获取成员列表
        members = db.query(
            EnterpriseMember, User, Role
        ).join(
            User, User.id == EnterpriseMember.user_id
        ).join(
            Role, Role.id == EnterpriseMember.role_id
        ).filter(
            EnterpriseMember.enterprise_id == enterprise_id
        ).all()

        result = []
        for member, user_obj, role in members:
            result.append({
                'id': member.id,
                'user_id': user_obj.id,
                'username': user_obj.username,
                'email': user_obj.email,
                'full_name': user_obj.full_name,
                'role_id': role.id,
                'role_code': role.code,
                'role_name': role.name,
                'status': member.status,
                'joined_at': member.joined_at.isoformat() if member.joined_at else None
            })

        return jsonify({
            'success': True,
            'members': result,
            'count': len(result)
        })

    finally:
        db.close()


@enterprise_bp.route('/<int:enterprise_id>/members', methods=['POST'])
@require_enterprise_role(['enterprise_owner', 'enterprise_admin'])
def add_member(enterprise_id):
    """添加企业成员"""
    data = request.json

    if not data.get('user_id') or not data.get('role_code'):
        return jsonify({
            'success': False,
            'error': '用户ID和角色代码不能为空'
        }), 400

    db = get_db_session()
    try:
        # 检查企业是否存在
        enterprise = db.query(Enterprise).filter_by(id=enterprise_id).first()
        if not enterprise:
            return jsonify({
                'success': False,
                'error': '企业不存在'
            }), 404

        # 检查用户是否存在
        target_user = db.query(User).filter_by(id=data['user_id']).first()
        if not target_user:
            return jsonify({
                'success': False,
                'error': '用户不存在'
            }), 404

        # 检查是否已是成员
        existing = db.query(EnterpriseMember).filter(
            EnterpriseMember.enterprise_id == enterprise_id,
            EnterpriseMember.user_id == data['user_id']
        ).first()

        if existing:
            return jsonify({
                'success': False,
                'error': '用户已是企业成员'
            }), 400

        # 检查成员数量限制
        member_count = db.query(EnterpriseMember).filter(
            EnterpriseMember.enterprise_id == enterprise_id,
            EnterpriseMember.status == 'active'
        ).count()

        if member_count >= enterprise.max_members:
            return jsonify({
                'success': False,
                'error': f'企业成员已达上限({enterprise.max_members})'
            }), 400

        # 获取角色
        role = db.query(Role).filter_by(code=data['role_code']).first()
        if not role:
            return jsonify({
                'success': False,
                'error': '角色不存在'
            }), 404

        # 添加成员
        member = EnterpriseMember(
            enterprise_id=enterprise_id,
            user_id=data['user_id'],
            role_id=role.id,
            status='active'
        )
        db.add(member)

        # 更新用户类型
        if target_user.user_type == 'individual':
            target_user.user_type = 'enterprise'

        db.commit()

        return jsonify({
            'success': True,
            'message': '成员添加成功',
            'member': member.to_dict()
        })

    except Exception as e:
        db.rollback()
        return jsonify({
            'success': False,
            'error': f'添加成员失败: {str(e)}'
        }), 500
    finally:
        db.close()


@enterprise_bp.route('/<int:enterprise_id>/members/<int:user_id>', methods=['PUT'])
@require_enterprise_role(['enterprise_owner', 'enterprise_admin'])
def update_member_role(enterprise_id, user_id):
    """更新成员角色"""
    data = request.json

    if not data.get('role_code'):
        return jsonify({
            'success': False,
            'error': '角色代码不能为空'
        }), 400

    db = get_db_session()
    try:
        member = db.query(EnterpriseMember).filter(
            EnterpriseMember.enterprise_id == enterprise_id,
            EnterpriseMember.user_id == user_id
        ).first()

        if not member:
            return jsonify({
                'success': False,
                'error': '成员不存在'
            }), 404

        # 获取新角色
        role = db.query(Role).filter_by(code=data['role_code']).first()
        if not role:
            return jsonify({
                'success': False,
                'error': '角色不存在'
            }), 404

        member.role_id = role.id
        db.commit()

        return jsonify({
            'success': True,
            'message': '角色更新成功',
            'member': member.to_dict()
        })

    except Exception as e:
        db.rollback()
        return jsonify({
            'success': False,
            'error': f'更新失败: {str(e)}'
        }), 500
    finally:
        db.close()


@enterprise_bp.route('/<int:enterprise_id>/members/<int:user_id>', methods=['DELETE'])
@require_enterprise_role(['enterprise_owner', 'enterprise_admin'])
def remove_member(enterprise_id, user_id):
    """移除企业成员"""
    current_user = get_current_user()

    # 不能移除自己
    if current_user.id == user_id:
        return jsonify({
            'success': False,
            'error': '不能移除自己'
        }), 400

    db = get_db_session()
    try:
        member = db.query(EnterpriseMember).filter(
            EnterpriseMember.enterprise_id == enterprise_id,
            EnterpriseMember.user_id == user_id
        ).first()

        if not member:
            return jsonify({
                'success': False,
                'error': '成员不存在'
            }), 404

        # 标记为已离开
        member.status = 'left'
        db.commit()

        return jsonify({
            'success': True,
            'message': '成员已移除'
        })

    except Exception as e:
        db.rollback()
        return jsonify({
            'success': False,
            'error': f'移除失败: {str(e)}'
        }), 500
    finally:
        db.close()


# ==================== 企业统计接口 ====================

@enterprise_bp.route('/<int:enterprise_id>/stats', methods=['GET'])
def get_enterprise_stats(enterprise_id):
    """获取企业统计信息"""
    user = get_current_user()

    if not user:
        return jsonify({
            'success': False,
            'error': '未登录'
        }), 401

    db = get_db_session()
    try:
        # 检查权限
        if not is_platform_admin(user):
            member = db.query(EnterpriseMember).filter(
                EnterpriseMember.enterprise_id == enterprise_id,
                EnterpriseMember.user_id == user.id,
                EnterpriseMember.status == 'active'
            ).first()

            if not member:
                return jsonify({
                    'success': False,
                    'error': '无权访问该企业'
                }), 403

        # 统计数据
        stats = {}

        # 成员数量
        stats['total_members'] = db.query(EnterpriseMember).filter(
            EnterpriseMember.enterprise_id == enterprise_id,
            EnterpriseMember.status == 'active'
        ).count()

        # 工作流数量
        stats['total_workflows'] = db.query(Workflow).filter(
            Workflow.enterprise_id == enterprise_id
        ).count()

        # 按角色统计成员
        role_stats = db.query(
            Role.name, db.func.count(EnterpriseMember.id)
        ).join(
            EnterpriseMember, EnterpriseMember.role_id == Role.id
        ).filter(
            EnterpriseMember.enterprise_id == enterprise_id,
            EnterpriseMember.status == 'active'
        ).group_by(Role.name).all()

        stats['members_by_role'] = {name: count for name, count in role_stats}

        return jsonify({
            'success': True,
            'stats': stats
        })

    finally:
        db.close()
