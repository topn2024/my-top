"""
添加用户角色字段并更新现有用户
"""
import sys
import io

# Windows控制台编码修复
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from models import SessionLocal, User, engine
from sqlalchemy import text
from werkzeug.security import generate_password_hash

def add_role_column():
    """添加role列到users表"""
    session = SessionLocal()

    try:
        # 检查role列是否已存在
        result = session.execute(text("PRAGMA table_info(users)"))
        columns = [row[1] for row in result]

        if 'role' in columns:
            print('✅ role列已存在')
        else:
            # 添加role列，默认值为'user'
            print('📝 添加role列到users表...')
            session.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user'"))
            session.commit()
            print('✅ role列添加成功')

        # 更新现有的admin用户为admin角色
        admin_user = session.query(User).filter_by(username='admin').first()
        if admin_user:
            session.execute(
                text("UPDATE users SET role = 'admin' WHERE username = 'admin'")
            )
            session.commit()
            print('✅ admin用户角色已设置为 admin')

        # 更新其他所有用户为user角色
        session.execute(
            text("UPDATE users SET role = 'user' WHERE role IS NULL OR role = ''")
        )
        session.commit()
        print('✅ 所有用户角色已初始化')

        # 显示所有用户及其角色
        print('\n📋 当前用户列表:')
        users = session.query(User).all()
        for user in users:
            result = session.execute(
                text(f"SELECT role FROM users WHERE id = {user.id}")
            )
            role = result.fetchone()[0] if result else 'user'
            print(f'  - {user.username}: {role}')

    except Exception as e:
        session.rollback()
        print(f'❌ 错误: {str(e)}')
        raise
    finally:
        session.close()

if __name__ == '__main__':
    add_role_column()
