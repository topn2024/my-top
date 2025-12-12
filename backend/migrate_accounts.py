#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
账号数据迁移脚本
将 accounts.json 中的账号迁移到 MySQL
"""
import json
import os
import sys
import shutil
from models import User, PlatformAccount, get_db_session
from encryption import encrypt_password


def migrate_accounts(admin_user_id=1):
    """
    迁移账号数据

    Args:
        admin_user_id: 管理员用户ID（默认为1）
    """
    # 查找 accounts.json 文件
    accounts_file = os.path.join(os.path.dirname(__file__), '..', 'accounts', 'accounts.json')

    if not os.path.exists(accounts_file):
        print(f"✗ 未找到账号文件: {accounts_file}")
        print(f"  跳过账号迁移")
        return True

    print(f"找到账号文件: {accounts_file}")

    # 读取账号数据
    try:
        with open(accounts_file, 'r', encoding='utf-8') as f:
            accounts_data = json.load(f)
    except Exception as e:
        print(f"✗ 读取账号文件失败: {e}")
        return False

    if not accounts_data:
        print("账号文件为空，无需迁移")
        return True

    print(f"共找到 {len(accounts_data)} 个平台账号")

    # 迁移账号
    db = get_db_session()
    migrated_count = 0
    skipped_count = 0

    try:
        for account_data in accounts_data:
            platform = account_data.get('platform', '')
            username = account_data.get('username', '')
            password = account_data.get('password', '')
            notes = account_data.get('notes', '')

            if not platform or not username:
                print(f"  ✗ 跳过无效账号: {account_data}")
                skipped_count += 1
                continue

            # 检查是否已存在
            existing = db.query(PlatformAccount).filter_by(
                user_id=admin_user_id,
                platform=platform,
                username=username
            ).first()

            if existing:
                print(f"  - {platform} / {username} 已存在，跳过")
                skipped_count += 1
                continue

            # 加密密码
            encrypted_password = encrypt_password(password)

            # 创建账号记录
            account = PlatformAccount(
                user_id=admin_user_id,
                platform=platform,
                username=username,
                password_encrypted=encrypted_password,
                notes=notes,
                status='active'
            )

            db.add(account)
            migrated_count += 1
            print(f"  ✓ {platform} / {username}")

        db.commit()

        print(f"\n迁移完成:")
        print(f"  成功迁移: {migrated_count} 个账号")
        print(f"  跳过: {skipped_count} 个账号")

        # 备份原文件
        backup_file = accounts_file + '.backup'
        if not os.path.exists(backup_file):
            shutil.copy2(accounts_file, backup_file)
            print(f"\n✓ 原文件已备份到: {backup_file}")

        return True

    except Exception as e:
        db.rollback()
        print(f"\n✗ 迁移失败: {e}")
        return False

    finally:
        db.close()


def main():
    """主函数"""
    print("=" * 60)
    print("账号数据迁移")
    print("=" * 60)

    # 确认管理员用户存在
    db = get_db_session()
    try:
        admin_user = db.query(User).filter_by(username='admin').first()
        if not admin_user:
            print("\n✗ 未找到管理员用户")
            print("  请先运行 create_admin.py 创建管理员账号")
            sys.exit(1)

        print(f"\n找到管理员用户: {admin_user.username} (ID: {admin_user.id})")

        # 执行迁移
        print("\n开始迁移账号数据...")
        success = migrate_accounts(admin_user.id)

        if success:
            print("\n" + "=" * 60)
            print("✓ 账号迁移完成!")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("✗ 账号迁移失败")
            print("=" * 60)
            sys.exit(1)

    finally:
        db.close()


if __name__ == '__main__':
    main()
