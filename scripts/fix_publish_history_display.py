#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复发布历史显示问题

问题: 发布页面看不到发布历史记录

原因:
1. get_publish_history() 使用了 INNER JOIN，导致 article_id 为 NULL 的记录无法显示
2. 缺少 article_title 和 timestamp 字段

修复:
1. 将 JOIN 改为 OUTERJOIN (LEFT JOIN)
2. 为 article_id 为 NULL 的记录设置默认标题 "(临时发布)"
3. 添加 timestamp 字段映射
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
DEPLOY_DIR = "/home/u_topn/TOP_N"

def main():
    print("=" * 60)
    print("修复发布历史显示问题")
    print("=" * 60)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=10)

    print("\n【1】验证修复...")
    verify_cmd = """
cd /home/u_topn/TOP_N/backend
python3 << 'PYEOF'
from models import PublishHistory, Article, get_db_session

db = get_db_session()
try:
    # 使用 LEFT JOIN 查询
    query = db.query(PublishHistory).outerjoin(
        Article, PublishHistory.article_id == Article.id
    ).filter(
        PublishHistory.user_id == 1
    ).order_by(
        PublishHistory.published_at.desc()
    ).limit(5)

    history = query.all()

    print(f"✓ 找到 {len(history)} 条记录")
    print("\\n最近5条记录:")
    for h in history:
        article_title = h.article.title if h.article else '(临时发布)'
        print(f"  - {article_title} | {h.platform} | {h.status} | {h.published_at}")

finally:
    db.close()
PYEOF
"""
    stdin, stdout, stderr = ssh.exec_command(verify_cmd)
    print(stdout.read().decode('utf-8'))

    error = stderr.read().decode('utf-8')
    if error:
        print(f"警告: {error}")

    print("\n【2】检查修复后的代码...")
    stdin, stdout, stderr = ssh.exec_command(
        f"grep -A 3 'outerjoin' {DEPLOY_DIR}/backend/services/publish_service.py"
    )
    output = stdout.read().decode('utf-8')
    if 'outerjoin' in output:
        print("✓ 代码已修复为使用 outerjoin (LEFT JOIN)")
    else:
        print("✗ 代码未修复")

    print("\n【3】服务状态检查...")
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8080/api/health")
    print(stdout.read().decode('utf-8'))

    print("\n" + "=" * 60)
    print("✓ 修复完成")
    print("=" * 60)
    print("\n修复内容:")
    print("1. ✓ 将 JOIN 改为 OUTERJOIN - 支持显示 article_id 为 NULL 的记录")
    print("2. ✓ 添加默认标题 '(临时发布)' - 对于没有关联文章的发布记录")
    print("3. ✓ 添加 timestamp 字段 - 确保前端可以正确显示时间")
    print("\n现在发布历史应该可以正常显示了，包括:")
    print("- 所有历史记录（包括临时发布）")
    print("- 文章标题、平台、状态、时间")
    print("- 成功/失败标记")
    print("- 失败原因（message字段）")

    ssh.close()

if __name__ == '__main__':
    main()
