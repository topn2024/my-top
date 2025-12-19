#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新models.py添加RBAC相关模型
"""
import sys
import os

# 添加backend目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def update_models_file():
    """更新models.py文件添加RBAC模型"""

    models_file = os.path.join(os.path.dirname(__file__), 'models.py')

    # 读取现有文件
    with open(models_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查是否已经更新过
    if 'class Enterprise(Base):' in content:
        print("✓ models.py 已经包含RBAC模型,无需更新")
        return

    print("开始更新models.py...")

    # 1. 在User类的字段定义之后(is_active之后)添加新字段
    user_fields_addition = """    user_type = Column(String(50), default='individual', index=True, comment='用户类型: individual, enterprise, system')
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=True, comment='系统级角色ID(仅用于admin等系统角色)')
"""

    # 查找is_active的位置
    is_active_pos = content.find("is_active = Column(Boolean, default=True)")
    if is_active_pos != -1:
        # 找到该行的结束位置
        line_end = content.find('\n', is_active_pos)
        # 插入新字段
        content = content[:line_end+1] + user_fields_addition + content[line_end+1:]
        print("✓ User模型: 添加user_type和role_id字段")

    # 2. 在User类的relationship部分添加新关系
    user_relationships_addition = """    role = relationship("Role", foreign_keys=[role_id])
    enterprise_memberships = relationship("EnterpriseMember", back_populates="user", cascade="all, delete-orphan")
"""

    # 查找publish_history relationship的位置
    publish_history_rel_pos = content.find('publish_history = relationship("PublishHistory"')
    if publish_history_rel_pos != -1:
        # 找到该行的结束位置
        line_end = content.find('\n', publish_history_rel_pos)
        # 插入新关系
        content = content[:line_end+1] + user_relationships_addition + content[line_end+1:]
        print("✓ User模型: 添加新的relationship")

    # 3. 在Workflow类添加新字段
    workflow_fields_addition = """    enterprise_id = Column(Integer, ForeignKey('enterprises.id'), nullable=True, index=True, comment='所属企业ID(企业用户创建)')
    visibility = Column(String(50), default='private', index=True, comment='可见性: private, team, public')
"""

    # 查找user_id定义的位置（在Workflow类中）
    workflow_user_id_pos = content.find("user_id = Column(Integer, ForeignKey('users.id'", is_active_pos)
    if workflow_user_id_pos != -1:
        # 找到该行的结束位置
        line_end = content.find('\n', workflow_user_id_pos)
        # 插入新字段
        content = content[:line_end+1] + workflow_fields_addition + content[line_end+1:]
        print("✓ Workflow模型: 添加enterprise_id和visibility字段")

    # 4. 在Workflow的relationship部分添加enterprise关系
    workflow_relationships_addition = """    enterprise = relationship("Enterprise", foreign_keys=[enterprise_id])
"""

    # 查找Workflow的user relationship
    workflow_user_rel_pos = content.find('user = relationship("User"', workflow_user_id_pos)
    if workflow_user_rel_pos != -1:
        # 找到该行的结束位置
        line_end = content.find('\n', workflow_user_rel_pos)
        # 插入新关系
        content = content[:line_end+1] + workflow_relationships_addition + content[line_end+1:]
        print("✓ Workflow模型: 添加enterprise relationship")

    # 5. 在文件末尾添加所有新的RBAC模型
    rbac_models = '''

# ==================== RBAC 权限管理模型 ====================

class Enterprise(Base):
    """企业表"""
    __tablename__ = 'enterprises'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, comment='企业名称')
    code = Column(String(50), unique=True, nullable=False, index=True, comment='企业唯一标识码')
    industry = Column(String(100), comment='所属行业')
    description = Column(Text, comment='企业描述')
    logo_url = Column(String(500), comment='企业Logo')
    contact_email = Column(String(100), comment='联系邮箱')
    contact_phone = Column(String(20), comment='联系电话')
    status = Column(String(50), default='active', index=True, comment='状态: active, suspended, closed')
    max_members = Column(Integer, default=10, comment='最大成员数限制')
    subscription_plan = Column(String(50), default='free', comment='订阅计划: free, basic, pro, enterprise')
    subscription_expires_at = Column(TIMESTAMP, nullable=True, comment='订阅到期时间')
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # 关系
    members = relationship("EnterpriseMember", back_populates="enterprise", cascade="all, delete-orphan")
    workflows = relationship("Workflow", foreign_keys='Workflow.enterprise_id', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Enterprise(id={self.id}, name='{self.name}', code='{self.code}')>"

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'industry': self.industry,
            'description': self.description,
            'logo_url': self.logo_url,
            'contact_email': self.contact_email,
            'contact_phone': self.contact_phone,
            'status': self.status,
            'max_members': self.max_members,
            'subscription_plan': self.subscription_plan,
            'subscription_expires_at': self.subscription_expires_at.isoformat() if self.subscription_expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Role(Base):
    """角色表"""
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment='角色名称')
    code = Column(String(50), unique=True, nullable=False, index=True, comment='角色代码')
    type = Column(String(50), nullable=False, index=True, comment='角色类型: system, enterprise, individual')
    description = Column(Text, comment='角色描述')
    is_system = Column(Boolean, default=False, comment='是否系统角色')
    created_at = Column(TIMESTAMP, server_default=func.now())

    # 关系
    permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}', code='{self.code}', type='{self.type}')>"

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'type': self.type,
            'description': self.description,
            'is_system': self.is_system,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Permission(Base):
    """权限表"""
    __tablename__ = 'permissions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    resource = Column(String(50), nullable=False, index=True, comment='资源类型')
    action = Column(String(50), nullable=False, index=True, comment='操作类型')
    code = Column(String(100), unique=True, nullable=False, index=True, comment='权限代码')
    description = Column(Text, comment='权限描述')
    created_at = Column(TIMESTAMP, server_default=func.now())

    # 关系
    roles = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Permission(id={self.id}, code='{self.code}', resource='{self.resource}', action='{self.action}')>"

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'resource': self.resource,
            'action': self.action,
            'code': self.code,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class RolePermission(Base):
    """角色-权限关联表"""
    __tablename__ = 'role_permissions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey('roles.id', ondelete='CASCADE'), nullable=False, index=True)
    permission_id = Column(Integer, ForeignKey('permissions.id', ondelete='CASCADE'), nullable=False, index=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # 关系
    role = relationship("Role", back_populates="permissions")
    permission = relationship("Permission", back_populates="roles")

    def __repr__(self):
        return f"<RolePermission(role_id={self.role_id}, permission_id={self.permission_id})>"

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'role_id': self.role_id,
            'permission_id': self.permission_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class EnterpriseMember(Base):
    """企业成员表"""
    __tablename__ = 'enterprise_members'

    id = Column(Integer, primary_key=True, autoincrement=True)
    enterprise_id = Column(Integer, ForeignKey('enterprises.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False, comment='企业内角色')
    status = Column(String(50), default='active', index=True, comment='状态: active, suspended, left')
    joined_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # 关系
    enterprise = relationship("Enterprise", back_populates="members")
    user = relationship("User", back_populates="enterprise_memberships")
    role = relationship("Role")

    def __repr__(self):
        return f"<EnterpriseMember(enterprise_id={self.enterprise_id}, user_id={self.user_id}, role_id={self.role_id})>"

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'enterprise_id': self.enterprise_id,
            'user_id': self.user_id,
            'role_id': self.role_id,
            'status': self.status,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
'''

    # 添加RBAC模型到文件末尾
    content += rbac_models
    print("✓ 添加5个新的RBAC模型类")

    # 写入更新后的文件
    with open(models_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print("\n" + "=" * 60)
    print("✓ models.py 更新完成!")
    print("=" * 60)
    print("\n更新内容:")
    print("  1. User模型: 添加user_type和role_id字段")
    print("  2. User模型: 添加role和enterprise_memberships关系")
    print("  3. Workflow模型: 添加enterprise_id和visibility字段")
    print("  4. Workflow模型: 添加enterprise关系")
    print("  5. 新增Enterprise模型")
    print("  6. 新增Role模型")
    print("  7. 新增Permission模型")
    print("  8. 新增RolePermission模型")
    print("  9. 新增EnterpriseMember模型")
    print("\n下一步: 上传更新后的models.py到服务器")


if __name__ == '__main__':
    update_models_file()
