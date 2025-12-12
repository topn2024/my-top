#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整部署发布历史管理功能
"""
import paramiko
import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

def create_backend_api_file(sftp):
    """创建后端API文件"""
    print("创建后端API文件...")

    # 使用本地文件
    local_path = 'D:/work/code/TOP_N/temp_api.py'
    remote_path = '/home/u_topn/TOP_N/backend/publish_history_api.py'

    api_content = """# -*- coding: utf-8 -*-
import sqlite3
from datetime import datetime

PUBLISH_HISTORY_DB = '/home/u_topn/TOP_N/backend/publish_history.db'

def get_db_connection():
    conn = sqlite3.connect(PUBLISH_HISTORY_DB)
    conn.row_factory = sqlite3.Row
    return conn

def save_publish_history(title, content, platform, account_username, status,
                         article_url=None, error_message=None, article_type=None,
                         publish_user='system'):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        word_count = len(content) if content else 0
        cursor.execute('''
            INSERT INTO publish_history
            (title, content, platform, account_username, status, article_url,
             error_message, article_type, word_count, publish_user)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, content, platform, account_username, status, article_url,
              error_message, article_type, word_count, publish_user))
        conn.commit()
        history_id = cursor.lastrowid
        conn.close()
        return history_id
    except Exception as e:
        print(f"保存发布历史失败: {e}")
        return None
"""

    with open(local_path, 'w', encoding='utf-8') as f:
        f.write(api_content)

    sftp.put(local_path, remote_path)
    print("✓ API文件已创建")

def integrate_api_to_app(ssh):
    """集成API到主应用"""
    print("\n集成API到主应用...")

    # 在app_with_upload.py末尾添加import
    cmd = """cat >> /home/u_topn/TOP_N/backend/app_with_upload.py << 'ENDIMPORT'

# 导入发布历史API
from publish_history_api import save_publish_history, get_db_connection
ENDIMPORT"""
    ssh.exec_command(cmd, timeout=10)

    # 添加路由
    cmd2 = """cat >> /home/u_topn/TOP_N/backend/app_with_upload.py << 'ENDROUTES'

@app.route('/publish-history')
def publish_history_page():
    return render_template('publish_history.html')

@app.route('/api/publish-history', methods=['GET'])
def get_publish_history():
    from flask import jsonify, request
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        status = request.args.get('status', '')
        platform = request.args.get('platform', '')

        conn = get_db_connection()
        cursor = conn.cursor()

        where_clauses = []
        params = []

        if status:
            where_clauses.append('status = ?')
            params.append(status)

        if platform:
            where_clauses.append('platform = ?')
            params.append(platform)

        where_sql = ' AND '.join(where_clauses) if where_clauses else '1=1'

        cursor.execute(f'SELECT COUNT(*) FROM publish_history WHERE {where_sql}', params)
        total = cursor.fetchone()[0]

        offset = (page - 1) * page_size
        query = f'SELECT * FROM publish_history WHERE {where_sql} ORDER BY publish_time DESC LIMIT ? OFFSET ?'
        cursor.execute(query, params + [page_size, offset])

        records = []
        for row in cursor.fetchall():
            records.append({
                'id': row['id'],
                'title': row['title'],
                'content': row['content'][:200] + '...' if row['content'] and len(row['content']) > 200 else row['content'],
                'platform': row['platform'],
                'account_username': row['account_username'],
                'status': row['status'],
                'article_url': row['article_url'],
                'error_message': row['error_message'],
                'publish_time': row['publish_time'],
                'article_type': row['article_type'],
                'word_count': row['word_count'],
                'publish_user': row['publish_user']
            })

        conn.close()

        return jsonify({
            'success': True,
            'data': records,
            'total': total,
            'page': page,
            'page_size': page_size
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/publish-history/<int:history_id>', methods=['GET'])
def get_publish_detail(history_id):
    from flask import jsonify
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM publish_history WHERE id = ?', (history_id,))
        row = cursor.fetchone()

        if not row:
            return jsonify({'success': False, 'message': '记录不存在'}), 404

        record = {
            'id': row['id'],
            'title': row['title'],
            'content': row['content'],
            'platform': row['platform'],
            'account_username': row['account_username'],
            'status': row['status'],
            'article_url': row['article_url'],
            'error_message': row['error_message'],
            'publish_time': row['publish_time'],
            'article_type': row['article_type'],
            'word_count': row['word_count'],
            'publish_user': row['publish_user']
        }

        conn.close()

        return jsonify({'success': True, 'data': record})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/publish-history/<int:history_id>', methods=['DELETE'])
def delete_publish_history(history_id):
    from flask import jsonify
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM publish_history WHERE id = ?', (history_id,))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({'success': False, 'message': '记录不存在'}), 404

        conn.close()

        return jsonify({'success': True, 'message': '删除成功'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/publish-history/stats', methods=['GET'])
def get_publish_stats():
    from flask import jsonify
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM publish_history')
        total = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM publish_history WHERE status = "success"')
        success_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM publish_history WHERE status = "failed"')
        failed_count = cursor.fetchone()[0]

        cursor.execute('SELECT platform, COUNT(*) as count FROM publish_history GROUP BY platform')
        platform_stats = [{'platform': row[0], 'count': row[1]} for row in cursor.fetchall()]

        cursor.execute('''
            SELECT DATE(publish_time) as date, COUNT(*) as count
            FROM publish_history
            WHERE publish_time >= datetime('now', '-7 days')
            GROUP BY DATE(publish_time)
            ORDER BY date DESC
        ''')
        recent_trend = [{'date': row[0], 'count': row[1]} for row in cursor.fetchall()]

        conn.close()

        return jsonify({
            'success': True,
            'stats': {
                'total': total,
                'success': success_count,
                'failed': failed_count,
                'success_rate': round(success_count / total * 100, 2) if total > 0 else 0,
                'platform_stats': platform_stats,
                'recent_trend': recent_trend
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
ENDROUTES"""
    ssh.exec_command(cmd2, timeout=10)
    print("✓ API已集成到主应用")

try:
    print("=" * 80)
    print("部署发布历史管理功能")
    print("=" * 80)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
    print("✓ SSH连接成功\n")

    sftp = ssh.open_sftp()

    # 步骤1: 创建API文件
    create_backend_api_file(sftp)

    # 步骤2: 集成到主应用
    integrate_api_to_app(ssh)

    # 步骤3: 添加首页链接
    print("\n添加导航链接...")
    cmd = """grep -q '发布历史' /home/u_topn/TOP_N/templates/index.html || sed -i '/<a href="\/accounts"/a\                <a href="/publish-history" class="btn">📊 发布历史</a>' /home/u_topn/TOP_N/templates/index.html"""
    ssh.exec_command(cmd, timeout=10)
    print("✓ 导航链接已添加")

    # 步骤4: 重启服务
    print("\n重启服务...")
    cmd = "sudo systemctl restart topn"
    ssh.exec_command(cmd, timeout=30)

    time.sleep(4)

    # 检查服务状态
    cmd = "sudo systemctl status topn --no-pager | head -15"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    print(stdout.read().decode('utf-8'))

    print("\n" + "=" * 80)
    print("✅ 发布历史管理功能部署完成!")
    print("=" * 80)
    print("""
后端API已部署 - 已集成到 app_with_upload.py
数据库已创建 - publish_history.db
导航链接已添加

下一步需要创建前端页面文件。
    """)

    sftp.close()
    ssh.close()

except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
