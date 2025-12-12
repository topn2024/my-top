#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试发布页面文章加载功能
"""

import paramiko
import sys
import io

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

SERVER = "39.105.12.124"
USER = "u_topn"
PASSWORD = "TopN@2024"

def main():
    print("=" * 60)
    print("测试发布页面文章加载")
    print("=" * 60)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=10)

    print("\n【1】检查数据库配置")
    check_db_cmd = """
python3 << 'PYEOF'
import sys
sys.path.insert(0, '/home/u_topn/TOP_N/backend')

from models import get_db_session, Article, User
db = get_db_session()

# 获取所有用户
users = db.query(User).all()
print(f"数据库中有 {len(users)} 个用户")

for user in users:
    article_count = db.query(Article).join(Article.workflow).filter_by(user_id=user.id).count()
    print(f"  - {user.username} (ID:{user.id}): {article_count} 篇文章")

db.close()
PYEOF
"""
    stdin, stdout, stderr = ssh.exec_command(check_db_cmd)
    print(stdout.read().decode('utf-8'))
    error = stderr.read().decode('utf-8')
    if error and 'warning' not in error.lower():
        print(f"错误: {error}")

    print("\n【2】测试文章API接口")
    test_api_cmd = """
# 使用测试用户登录并获取文章
python3 << 'PYEOF'
import requests

# 创建session
session = requests.Session()

# 登录
login_response = session.post('http://localhost:8080/api/login', json={
    'username': 'test_user',
    'password': 'test123'
})

print(f"登录状态码: {login_response.status_code}")
if login_response.status_code == 200:
    print("登录成功")

    # 获取文章
    articles_response = session.get('http://localhost:8080/api/articles/history?limit=20')
    print(f"\\n文章API状态码: {articles_response.status_code}")

    data = articles_response.json()
    print(f"返回数据: {data}")

    if data.get('success'):
        print(f"\\n成功获取 {len(data.get('articles', []))} 篇文章")
        for i, article in enumerate(data.get('articles', [])[:3], 1):
            print(f"  {i}. {article.get('title', 'N/A')}")
    else:
        print(f"获取失败: {data.get('error', 'Unknown')}")
else:
    print(f"登录失败: {login_response.text}")
PYEOF
"""
    stdin, stdout, stderr = ssh.exec_command(test_api_cmd)
    print(stdout.read().decode('utf-8'))
    error = stderr.read().decode('utf-8')
    if error and 'warning' not in error.lower():
        print(f"错误: {error}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

    ssh.close()

if __name__ == '__main__':
    main()
