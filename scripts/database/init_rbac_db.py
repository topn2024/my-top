#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RBAC权限系统数据库初始化脚本
创建新表并初始化系统角色和权限
"""
import sys
import os

# 添加backend目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_db_session
from sqlalchemy import text

# 数据库连接
db = get_db_session()

def create_tables():
    """创建RBAC相关表"""
    print("=" * 60)
    print("开始创建RBAC权限系统表...")
    print("=" * 60)

    # 1. 创建企业表
    print("\n[1/5] 创建企业表 (enterprises)...")
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS enterprises (
            id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(200) NOT NULL COMMENT '企业名称',
            code VARCHAR(50) UNIQUE NOT NULL COMMENT '企业唯一标识码',
            industry VARCHAR(100) COMMENT '所属行业',
            description TEXT COMMENT '企业描述',
            logo_url VARCHAR(500) COMMENT '企业Logo',
            contact_email VARCHAR(100) COMMENT '联系邮箱',
            contact_phone VARCHAR(20) COMMENT '联系电话',
            status VARCHAR(50) DEFAULT 'active' COMMENT '状态: active, suspended, closed',
            max_members INT DEFAULT 10 COMMENT '最大成员数限制',
            subscription_plan VARCHAR(50) DEFAULT 'free' COMMENT '订阅计划: free, basic, pro, enterprise',
            subscription_expires_at TIMESTAMP NULL COMMENT '订阅到期时间',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_code (code),
            INDEX idx_status (status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='企业表'
    """))
    db.commit()
    print("✓ 企业表创建成功")

    # 2. 创建角色表
    print("\n[2/5] 创建角色表 (roles)...")
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS roles (
            id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(50) NOT NULL COMMENT '角色名称',
            code VARCHAR(50) UNIQUE NOT NULL COMMENT '角色代码',
            type VARCHAR(50) NOT NULL COMMENT '角色类型: system, enterprise, individual',
            description TEXT COMMENT '角色描述',
            is_system BOOLEAN DEFAULT FALSE COMMENT '是否系统角色',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_code (code),
            INDEX idx_type (type)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色表'
    """))
    db.commit()
    print("✓ 角色表创建成功")

    # 3. 创建权限表
    print("\n[3/5] 创建权限表 (permissions)...")
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS permissions (
            id INT PRIMARY KEY AUTO_INCREMENT,
            resource VARCHAR(50) NOT NULL COMMENT '资源类型',
            action VARCHAR(50) NOT NULL COMMENT '操作类型',
            code VARCHAR(100) UNIQUE NOT NULL COMMENT '权限代码',
            description TEXT COMMENT '权限描述',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uk_resource_action (resource, action),
            INDEX idx_code (code)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='权限表'
    """))
    db.commit()
    print("✓ 权限表创建成功")

    # 4. 创建角色-权限关联表
    print("\n[4/5] 创建角色-权限关联表 (role_permissions)...")
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS role_permissions (
            id INT PRIMARY KEY AUTO_INCREMENT,
            role_id INT NOT NULL,
            permission_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
            FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE,
            UNIQUE KEY uk_role_permission (role_id, permission_id),
            INDEX idx_role_id (role_id),
            INDEX idx_permission_id (permission_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色权限关联表'
    """))
    db.commit()
    print("✓ 角色-权限关联表创建成功")

    # 5. 创建企业成员表
    print("\n[5/5] 创建企业成员表 (enterprise_members)...")
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS enterprise_members (
            id INT PRIMARY KEY AUTO_INCREMENT,
            enterprise_id INT NOT NULL,
            user_id INT NOT NULL,
            role_id INT NOT NULL COMMENT '企业内角色',
            status VARCHAR(50) DEFAULT 'active' COMMENT '状态: active, suspended, left',
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (enterprise_id) REFERENCES enterprises(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (role_id) REFERENCES roles(id),
            UNIQUE KEY uk_enterprise_user (enterprise_id, user_id),
            INDEX idx_enterprise_id (enterprise_id),
            INDEX idx_user_id (user_id),
            INDEX idx_status (status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='企业成员表'
    """))
    db.commit()
    print("✓ 企业成员表创建成功")

    print("\n" + "=" * 60)
    print("所有表创建完成!")
    print("=" * 60)


def update_existing_tables():
    """更新现有表结构"""
    print("\n" + "=" * 60)
    print("开始更新现有表结构...")
    print("=" * 60)

    # 更新 users 表
    print("\n[1/2] 更新 users 表...")
    try:
        # 检查字段是否已存在
        result = db.execute(text("""
            SELECT COUNT(*) as count FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'users'
            AND COLUMN_NAME = 'user_type'
        """))
        exists = result.fetchone()[0] > 0

        if not exists:
            db.execute(text("""
                ALTER TABLE users
                ADD COLUMN user_type VARCHAR(50) DEFAULT 'individual' COMMENT '用户类型: individual, enterprise' AFTER is_active,
                ADD COLUMN role_id INT NULL COMMENT '系统级角色(仅用于admin等系统角色)' AFTER user_type,
                ADD INDEX idx_user_type (user_type)
            """))
            db.commit()
            print("✓ users表字段添加成功")
        else:
            print("✓ users表字段已存在,跳过")
    except Exception as e:
        print(f"⚠ users表更新警告: {e}")
        db.rollback()

    # 更新 workflows 表
    print("\n[2/2] 更新 workflows 表...")
    try:
        result = db.execute(text("""
            SELECT COUNT(*) as count FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'workflows'
            AND COLUMN_NAME = 'enterprise_id'
        """))
        exists = result.fetchone()[0] > 0

        if not exists:
            db.execute(text("""
                ALTER TABLE workflows
                ADD COLUMN enterprise_id INT NULL COMMENT '所属企业ID(企业用户创建)' AFTER user_id,
                ADD COLUMN visibility VARCHAR(50) DEFAULT 'private' COMMENT '可见性: private, team, public' AFTER enterprise_id,
                ADD INDEX idx_enterprise_id (enterprise_id)
            """))
            db.commit()
            print("✓ workflows表字段添加成功")
        else:
            print("✓ workflows表字段已存在,跳过")
    except Exception as e:
        print(f"⚠ workflows表更新警告: {e}")
        db.rollback()

    print("\n" + "=" * 60)
    print("现有表更新完成!")
    print("=" * 60)


def init_system_roles():
    """初始化系统角色"""
    print("\n" + "=" * 60)
    print("开始初始化系统角色...")
    print("=" * 60)

    roles_data = [
        # 系统级角色
        ('SUPER_ADMIN', 'super_admin', 'system', '超级管理员 - 系统最高权限', True),
        ('PLATFORM_ADMIN', 'platform_admin', 'system', '平台管理员 - 管理平台用户和企业', True),

        # 企业级角色
        ('ENTERPRISE_OWNER', 'enterprise_owner', 'enterprise', '企业所有者 - 企业最高权限', True),
        ('ENTERPRISE_ADMIN', 'enterprise_admin', 'enterprise', '企业管理员 - 管理企业成员和权限', True),
        ('ENTERPRISE_MEMBER', 'enterprise_member', 'enterprise', '企业普通成员 - 基本使用权限', True),
        ('ENTERPRISE_VIEWER', 'enterprise_viewer', 'enterprise', '企业查看者 - 仅查看权限', True),

        # 个人用户角色
        ('INDIVIDUAL_USER', 'individual_user', 'individual', '个人用户 - 个人账号权限', True),
    ]

    for name, code, role_type, description, is_system in roles_data:
        # 检查角色是否已存在
        result = db.execute(text("""
            SELECT id FROM roles WHERE code = :code
        """), {'code': code})

        if result.fetchone():
            print(f"✓ 角色 {name} 已存在,跳过")
        else:
            db.execute(text("""
                INSERT INTO roles (name, code, type, description, is_system)
                VALUES (:name, :code, :type, :description, :is_system)
            """), {
                'name': name,
                'code': code,
                'type': role_type,
                'description': description,
                'is_system': is_system
            })
            db.commit()
            print(f"✓ 创建角色: {name}")

    print("\n" + "=" * 60)
    print("系统角色初始化完成!")
    print("=" * 60)


def init_permissions():
    """初始化权限"""
    print("\n" + "=" * 60)
    print("开始初始化权限...")
    print("=" * 60)

    # 资源和操作定义
    resources = [
        ('workflow', '工作流'),
        ('article', '文章'),
        ('platform_account', '平台账号'),
        ('user', '用户'),
        ('enterprise', '企业'),
        ('publish', '发布'),
        ('system', '系统')
    ]

    actions = [
        ('create', '创建'),
        ('read', '读取'),
        ('update', '更新'),
        ('delete', '删除'),
        ('execute', '执行'),
        ('manage', '管理')
    ]

    count = 0
    for resource, resource_name in resources:
        for action, action_name in actions:
            code = f"{resource}.{action}"
            description = f"{action_name}{resource_name}"

            # 检查权限是否已存在
            result = db.execute(text("""
                SELECT id FROM permissions WHERE code = :code
            """), {'code': code})

            if result.fetchone():
                pass  # 已存在,跳过
            else:
                db.execute(text("""
                    INSERT INTO permissions (resource, action, code, description)
                    VALUES (:resource, :action, :code, :description)
                """), {
                    'resource': resource,
                    'action': action,
                    'code': code,
                    'description': description
                })
                count += 1

    db.commit()
    print(f"✓ 创建了 {count} 个权限")

    print("\n" + "=" * 60)
    print("权限初始化完成!")
    print("=" * 60)


def assign_role_permissions():
    """为角色分配权限"""
    print("\n" + "=" * 60)
    print("开始为角色分配权限...")
    print("=" * 60)

    # 1. SUPER_ADMIN - 所有权限
    print("\n[1/7] 为SUPER_ADMIN分配所有权限...")
    db.execute(text("""
        INSERT IGNORE INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r
        CROSS JOIN permissions p
        WHERE r.code = 'super_admin'
    """))
    db.commit()
    print("✓ SUPER_ADMIN权限分配完成")

    # 2. PLATFORM_ADMIN - 用户和企业管理权限
    print("\n[2/7] 为PLATFORM_ADMIN分配权限...")
    db.execute(text("""
        INSERT IGNORE INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r
        CROSS JOIN permissions p
        WHERE r.code = 'platform_admin'
        AND p.resource IN ('user', 'enterprise', 'system')
    """))
    db.commit()
    print("✓ PLATFORM_ADMIN权限分配完成")

    # 3. ENTERPRISE_OWNER - 企业内所有权限
    print("\n[3/7] 为ENTERPRISE_OWNER分配权限...")
    db.execute(text("""
        INSERT IGNORE INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r
        CROSS JOIN permissions p
        WHERE r.code = 'enterprise_owner'
        AND p.resource IN ('workflow', 'article', 'platform_account', 'user', 'enterprise', 'publish')
    """))
    db.commit()
    print("✓ ENTERPRISE_OWNER权限分配完成")

    # 4. ENTERPRISE_ADMIN - 管理权限
    print("\n[4/7] 为ENTERPRISE_ADMIN分配权限...")
    db.execute(text("""
        INSERT IGNORE INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r
        CROSS JOIN permissions p
        WHERE r.code = 'enterprise_admin'
        AND (
            (p.resource IN ('workflow', 'article', 'platform_account', 'publish') AND p.action IN ('create', 'read', 'update', 'delete', 'execute'))
            OR (p.resource = 'user' AND p.action IN ('read', 'manage'))
            OR (p.resource = 'enterprise' AND p.action = 'read')
        )
    """))
    db.commit()
    print("✓ ENTERPRISE_ADMIN权限分配完成")

    # 5. ENTERPRISE_MEMBER - 基本使用权限
    print("\n[5/7] 为ENTERPRISE_MEMBER分配权限...")
    db.execute(text("""
        INSERT IGNORE INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r
        CROSS JOIN permissions p
        WHERE r.code = 'enterprise_member'
        AND (
            (p.resource IN ('workflow', 'article', 'platform_account') AND p.action IN ('create', 'read'))
            OR (p.resource = 'publish' AND p.action = 'execute')
        )
    """))
    db.commit()
    print("✓ ENTERPRISE_MEMBER权限分配完成")

    # 6. ENTERPRISE_VIEWER - 只读权限
    print("\n[6/7] 为ENTERPRISE_VIEWER分配权限...")
    db.execute(text("""
        INSERT IGNORE INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r
        CROSS JOIN permissions p
        WHERE r.code = 'enterprise_viewer'
        AND p.action = 'read'
    """))
    db.commit()
    print("✓ ENTERPRISE_VIEWER权限分配完成")

    # 7. INDIVIDUAL_USER - 个人用户权限
    print("\n[7/7] 为INDIVIDUAL_USER分配权限...")
    db.execute(text("""
        INSERT IGNORE INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r
        CROSS JOIN permissions p
        WHERE r.code = 'individual_user'
        AND p.resource IN ('workflow', 'article', 'platform_account', 'publish')
        AND p.action IN ('create', 'read', 'update', 'delete', 'execute')
    """))
    db.commit()
    print("✓ INDIVIDUAL_USER权限分配完成")

    print("\n" + "=" * 60)
    print("角色权限分配完成!")
    print("=" * 60)


def migrate_existing_users():
    """迁移现有用户"""
    print("\n" + "=" * 60)
    print("开始迁移现有用户...")
    print("=" * 60)

    # 1. 设置所有现有用户为individual类型
    print("\n[1/2] 设置现有用户为个人用户类型...")
    result = db.execute(text("""
        UPDATE users
        SET user_type = 'individual'
        WHERE user_type IS NULL OR user_type = ''
    """))
    db.commit()
    print(f"✓ 更新了 {result.rowcount} 个用户")

    # 2. 设置admin用户为系统管理员
    print("\n[2/2] 设置admin为超级管理员...")
    db.execute(text("""
        UPDATE users
        SET user_type = 'system',
            role_id = (SELECT id FROM roles WHERE code = 'super_admin' LIMIT 1)
        WHERE username = 'admin'
    """))
    db.commit()
    print("✓ admin用户已设置为超级管理员")

    print("\n" + "=" * 60)
    print("用户迁移完成!")
    print("=" * 60)


def show_summary():
    """显示统计信息"""
    print("\n" + "=" * 60)
    print("RBAC权限系统初始化完成!")
    print("=" * 60)

    # 统计信息
    result = db.execute(text("SELECT COUNT(*) FROM roles"))
    roles_count = result.fetchone()[0]

    result = db.execute(text("SELECT COUNT(*) FROM permissions"))
    permissions_count = result.fetchone()[0]

    result = db.execute(text("SELECT COUNT(*) FROM role_permissions"))
    role_permissions_count = result.fetchone()[0]

    result = db.execute(text("SELECT COUNT(*) FROM users"))
    users_count = result.fetchone()[0]

    print(f"\n📊 统计信息:")
    print(f"   - 角色数量: {roles_count}")
    print(f"   - 权限数量: {permissions_count}")
    print(f"   - 角色-权限关联: {role_permissions_count}")
    print(f"   - 用户数量: {users_count}")

    print(f"\n✅ 系统表:")
    print(f"   ✓ enterprises (企业表)")
    print(f"   ✓ roles (角色表)")
    print(f"   ✓ permissions (权限表)")
    print(f"   ✓ role_permissions (角色权限关联表)")
    print(f"   ✓ enterprise_members (企业成员表)")

    print(f"\n✅ 更新表:")
    print(f"   ✓ users (添加 user_type, role_id)")
    print(f"   ✓ workflows (添加 enterprise_id, visibility)")

    print(f"\n🎯 下一步:")
    print(f"   1. 更新 ORM 模型 (models.py)")
    print(f"   2. 创建权限验证装饰器")
    print(f"   3. 实现企业管理API")
    print(f"   4. 创建前端管理页面")

    print("\n" + "=" * 60)


def main():
    """主函数"""
    try:
        # 1. 创建新表
        create_tables()

        # 2. 更新现有表
        update_existing_tables()

        # 3. 初始化角色
        init_system_roles()

        # 4. 初始化权限
        init_permissions()

        # 5. 分配角色权限
        assign_role_permissions()

        # 6. 迁移现有用户
        migrate_existing_users()

        # 7. 显示统计信息
        show_summary()

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return 1
    finally:
        db.close()

    return 0


if __name__ == '__main__':
    exit(main())
