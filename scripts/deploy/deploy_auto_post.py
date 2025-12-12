#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署知乎自动发帖功能到TopN项目
"""
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

# Flask API代码 - 添加到app_with_upload.py
API_CODE = '''
# ========== 知乎自动发帖API ==========

@app.route('/api/zhihu/post', methods=['POST'])
def zhihu_post_article():
    """发布文章到知乎"""
    try:
        data = request.get_json() or {}

        username = data.get('username')  # 知乎账号
        title = data.get('title')
        content = data.get('content')
        topics = data.get('topics', [])  # 话题列表
        draft = data.get('draft', False)  # 是否保存为草稿

        if not username or not title or not content:
            return jsonify({
                'success': False,
                'message': '缺少必要参数: username, title, content'
            }), 400

        # 导入发帖模块
        from zhihu_auto_post import post_article_to_zhihu

        # 执行发帖
        result = post_article_to_zhihu(
            username=username,
            title=title,
            content=content,
            topics=topics,
            draft=draft
        )

        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 500

    except Exception as e:
        logger.error(f"Zhihu post error: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/zhihu/answer', methods=['POST'])
def zhihu_post_answer():
    """回答知乎问题"""
    try:
        data = request.get_json() or {}

        username = data.get('username')
        question_url = data.get('question_url')
        content = data.get('content')

        if not username or not question_url or not content:
            return jsonify({
                'success': False,
                'message': '缺少必要参数: username, question_url, content'
            }), 400

        # 导入发帖模块
        from zhihu_auto_post import ZhihuAutoPost

        poster = ZhihuAutoPost()

        try:
            if not poster.init_browser():
                return jsonify({'success': False, 'message': '浏览器初始化失败'}), 500

            if not poster.load_cookies(username):
                return jsonify({'success': False, 'message': 'Cookie加载失败'}), 500

            result = poster.create_answer(question_url, content)

            return jsonify(result)

        finally:
            poster.close()

    except Exception as e:
        logger.error(f"Zhihu answer error: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/articles/publish_to_zhihu/<int:article_id>', methods=['POST'])
def publish_article_to_zhihu(article_id):
    """将已生成的文章发布到知乎

    Args:
        article_id: 文章ID

    Request Body:
        {
            "username": "zhihu_account",  # 知乎账号
            "topics": ["Python", "AI"],   # 可选,话题列表
            "draft": false                 # 可选,是否保存为草稿
        }
    """
    try:
        data = request.get_json() or {}
        username = data.get('username')

        if not username:
            return jsonify({'success': False, 'message': '缺少知乎账号参数'}), 400

        # 从数据库或文件中获取文章内容
        # 这里需要根据实际的文章存储方式来实现
        # 示例: 假设文章存储在articles目录
        import os
        articles_dir = os.path.join(os.path.dirname(__file__), 'articles')
        article_file = os.path.join(articles_dir, f'article_{article_id}.json')

        if not os.path.exists(article_file):
            return jsonify({
                'success': False,
                'message': f'文章不存在: {article_id}'
            }), 404

        import json
        with open(article_file, 'r', encoding='utf-8') as f:
            article_data = json.load(f)

        title = article_data.get('title')
        content = article_data.get('content')

        if not title or not content:
            return jsonify({
                'success': False,
                'message': '文章数据不完整'
            }), 400

        # 发布到知乎
        from zhihu_auto_post import post_article_to_zhihu

        topics = data.get('topics', [])
        draft = data.get('draft', False)

        result = post_article_to_zhihu(
            username=username,
            title=title,
            content=content,
            topics=topics,
            draft=draft
        )

        # 更新文章发布状态
        if result.get('success'):
            article_data['published_to_zhihu'] = True
            article_data['zhihu_url'] = result.get('url')

            with open(article_file, 'w', encoding='utf-8') as f:
                json.dump(article_data, f, ensure_ascii=False, indent=2)

        return jsonify(result)

    except Exception as e:
        logger.error(f"Publish to Zhihu error: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500
'''

def main():
    try:
        print("="*80)
        print("部署知乎自动发帖功能")
        print("="*80)

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("✓ SSH连接成功\n")

        # 步骤1: 上传zhihu_auto_post.py模块
        print("[1/4] 上传自动发帖模块...")
        sftp = ssh.open_sftp()

        try:
            sftp.put('zhihu_auto_post.py', '/home/u_topn/TOP_N/backend/zhihu_auto_post.py')
            print("✓ zhihu_auto_post.py 已上传")
        except Exception as e:
            print(f"上传失败: {e}")
            return False

        sftp.close()

        # 步骤2: 设置执行权限
        print("\n[2/4] 设置文件权限...")
        cmd = "chmod +x /home/u_topn/TOP_N/backend/zhihu_auto_post.py"
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        stdout.read()
        print("✓ 权限已设置")

        # 步骤3: 在app_with_upload.py中添加API
        print("\n[3/4] 添加API接口...")

        # 备份
        cmd = "cp /home/u_topn/TOP_N/backend/app_with_upload.py /home/u_topn/TOP_N/backend/app_with_upload.py.backup_autopost"
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        stdout.read()

        # 使用Python脚本添加API代码
        add_api_script = f"""
import sys
sys.path.insert(0, '/home/u_topn/TOP_N/backend')

with open('/home/u_topn/TOP_N/backend/app_with_upload.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 检查是否已经添加过
if 'zhihu_post_article' in content:
    print('API已存在,跳过添加')
else:
    # 在if __name__ == '__main__'之前插入
    marker = "if __name__ == '__main__':"
    if marker in content:
        parts = content.split(marker)
        api_code = '''{API_CODE}'''
        new_content = parts[0] + api_code + "\\n\\n" + marker + parts[1]

        with open('/home/u_topn/TOP_N/backend/app_with_upload.py', 'w', encoding='utf-8') as f:
            f.write(new_content)

        print('✓ API代码已添加')
    else:
        print('✗ 未找到插入点')
"""

        cmd = f"python3 << 'PYEOF'\n{add_api_script}\nPYEOF"
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=20)
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        print(output)
        if error:
            print(f"错误: {error}")

        # 步骤4: 重启服务
        print("\n[4/4] 重启服务...")
        cmd = "sudo systemctl restart topn && sleep 3"
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)

        import time
        time.sleep(4)

        cmd = "sudo systemctl status topn --no-pager | head -15"
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        print(stdout.read().decode('utf-8'))

        print("\n" + "="*80)
        print("✅ 部署完成!")
        print("="*80)
        print("""
新增API接口:

1. POST /api/zhihu/post
   发布文章到知乎
   参数: {
       "username": "zhihu_account",
       "title": "文章标题",
       "content": "文章内容",
       "topics": ["话题1", "话题2"],  # 可选
       "draft": false                  # 可选,是否保存为草稿
   }

2. POST /api/zhihu/answer
   回答知乎问题
   参数: {
       "username": "zhihu_account",
       "question_url": "问题链接",
       "content": "回答内容"
   }

3. POST /api/articles/publish_to_zhihu/<article_id>
   将已生成的文章发布到知乎
   参数: {
       "username": "zhihu_account",
       "topics": ["话题1"],  # 可选
       "draft": false        # 可选
   }

使用示例:
curl -X POST http://39.105.12.124:8080/api/zhihu/post \\
  -H "Content-Type: application/json" \\
  -d '{
    "username": "your_account",
    "title": "测试文章",
    "content": "这是一篇测试文章...",
    "topics": ["Python", "编程"]
  }'

注意事项:
1. 需要先通过二维码登录保存Cookie
2. username参数对应已保存Cookie的账号
3. 发帖会打开浏览器窗口,可以看到实时过程
        """)

        ssh.close()
        return True

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()
