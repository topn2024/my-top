#!/usr/bin/env python3
"""
数据库初始化脚本
创建所有必需的表并初始化基本数据
"""
import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from models import Base, User, PlatformAccount, PublishHistory, PublishTask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from encryption import encrypt_password
from datetime import datetime

def init_database():
    """初始化数据库"""

    # 数据库路径
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'topn.db')
    db_dir = os.path.dirname(db_path)

    # 确保目录存在
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
        print(f'✓ 创建数据目录: {db_dir}')

    # 创建数据库引擎
    engine = create_engine(f'sqlite:///{db_path}')

    # 创建所有表
    print('正在创建数据库表...')
    Base.metadata.create_all(engine)
    print('✓ 数据库表创建完成')

    # 创建会话
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 检查是否已有admin用户
        admin = session.query(User).filter_by(username='admin').first()

        if not admin:
            # 创建admin用户
            admin = User(
                username='admin',
                password_hash='pbkdf2:sha256:260000$qwerty$hash',  # 默认密码需要改
                email='admin@example.com',
                full_name='Administrator',
                is_active=True
            )
            session.add(admin)
            session.commit()
            print(f'✓ 创建admin用户 (ID: {admin.id})')
        else:
            print(f'✓ admin用户已存在 (ID: {admin.id})')

        # 检查是否已有知乎账号配置
        zhihu_account = session.query(PlatformAccount).filter_by(
            user_id=admin.id,
            platform='zhihu'
        ).first()

        if not zhihu_account:
            # 创建知乎账号配置（使用默认密码，需要后续配置）
            zhihu_account = PlatformAccount(
                user_id=admin.id,
                platform='zhihu',
                username='admin',
                password_encrypted=encrypt_password('changeme'),  # 默认密码，需要修改
                status='active',
                notes='默认知乎账号，请在账号管理页面更新密码'
            )
            session.add(zhihu_account)
            session.commit()
            print(f'✓ 创建知乎账号配置 (ID: {zhihu_account.id}, Username: {zhihu_account.username})')
            print('  ⚠️  请在账号管理页面更新知乎账号的用户名和密码')
        else:
            print(f'✓ 知乎账号配置已存在 (ID: {zhihu_account.id}, Username: {zhihu_account.username})')

        # 显示表信息
        print('\n数据库表统计:')
        print(f'  用户数: {session.query(User).count()}')
        print(f'  平台账号数: {session.query(PlatformAccount).count()}')
        print(f'  发布历史数: {session.query(PublishHistory).count()}')
        print(f'  发布任务数: {session.query(PublishTask).count()}')

        print('\n✓ 数据库初始化完成！')
        print(f'  数据库文件: {db_path}')

    except Exception as e:
        print(f'✗ 初始化失败: {e}')
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == '__main__':
    init_database()
