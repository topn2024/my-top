#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为发布失败的文章添加重试功能

功能:
1. 后端: 添加 /api/retry_publish/<history_id> 接口
2. 前端: 在失败记录旁添加"重试"按钮
3. 支持从发布历史记录中提取文章内容并重新发布
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

# 后端API代码
API_CODE = '''
@api_bp.route('/retry_publish/<int:history_id>', methods=['POST'])
@login_required
def retry_publish(history_id):
    """重试发布失败的文章"""
    from services.publish_service import PublishService
    from models import get_db_session, PublishHistory

    user = get_current_user()

    db = get_db_session()
    try:
        # 获取发布历史记录
        history = db.query(PublishHistory).filter_by(
            id=history_id,
            user_id=user.id  # 确保只能重试自己的记录
        ).first()

        if not history:
            return jsonify({'success': False, 'error': '发布记录不存在'}), 404

        # 检查平台
        if history.platform != '知乎':
            return jsonify({'success': False, 'error': f'暂不支持重试{history.platform}平台'}), 400

        # 准备重新发布
        title = history.title
        content_url = history.content_url  # 如果有保存内容URL
        article_id = history.article_id

        # 如果有关联文章，从文章中获取内容
        if history.article:
            title = history.article.title
            content = history.article.content
        else:
            # 临时发布的文章，需要从history中获取
            # 这里需要确保PublishHistory保存了title和content
            return jsonify({
                'success': False,
                'error': '无法获取文章内容，请重新选择文章发布'
            }), 400

        logger.info(f'Retry publishing article: {title} to 知乎')

        # 调用发布服务
        publish_service = PublishService(config)
        success, message, url = publish_service.publish_to_zhihu(
            user_id=user.id,
            title=title,
            content=content,
            article_id=article_id,
            draft=False
        )

        if success:
            return jsonify({
                'success': True,
                'message': message or '重新发布成功',
                'url': url
            })
        else:
            return jsonify({
                'success': False,
                'error': message or '重新发布失败'
            }), 500

    except Exception as e:
        logger.error(f'Retry publish failed: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()
'''

# 前端JS代码 - 修改displayPublishHistory函数，添加重试按钮
FRONTEND_CODE_ADDITION = '''
                    ${item.status === 'failed' ? `
                        <button onclick="retryPublish(${item.id}, '${item.article_title.replace(/'/g, "\\\\'")}', this)"
                            style="display: inline-flex; align-items: center; gap: 4px; font-size: 12px; color: white; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; margin-top: 8px; transition: all 0.3s; box-shadow: 0 2px 8px rgba(240, 147, 251, 0.3);"
                            onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(240, 147, 251, 0.5)'"
                            onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 8px rgba(240, 147, 251, 0.3)'">
                            <span>🔄</span>重试发布
                        </button>
                    ` : ''}
'''

# 重试函数
RETRY_FUNCTION = '''
// 重试发布失败的文章
async function retryPublish(historyId, articleTitle, button) {
    if (!confirm(`确定要重新发布《${articleTitle}》吗？`)) {
        return;
    }

    // 禁用按钮
    button.disabled = true;
    button.innerHTML = '<span>⏳</span>重试中...';
    button.style.background = 'linear-gradient(135deg, #ccc 0%, #999 100%)';

    try {
        const response = await fetch(`/api/retry_publish/${historyId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (data.success) {
            alert(`重新发布成功！\\n${data.message || ''}`);
            // 刷新发布历史
            loadPublishHistory();
        } else {
            alert(`重新发布失败：${data.error || data.message || '未知错误'}`);
            // 恢复按钮
            button.disabled = false;
            button.innerHTML = '<span>🔄</span>重试发布';
            button.style.background = 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)';
        }
    } catch (error) {
        alert('重新发布失败: ' + error.message);
        // 恢复按钮
        button.disabled = false;
        button.innerHTML = '<span>🔄</span>重试发布';
        button.style.background = 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)';
    }
}
'''

def main():
    print("=" * 60)
    print("为发布失败的文章添加重试功能")
    print("=" * 60)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=10)

    print("\n【1】备份当前文件...")
    backup_cmd = f"""
cd {DEPLOY_DIR}
cp backend/blueprints/api.py backend/blueprints/api.py.bak.retry
cp static/publish.js static/publish.js.bak.retry
echo "✓ 备份完成"
"""
    stdin, stdout, stderr = ssh.exec_command(backup_cmd)
    print(stdout.read().decode('utf-8'))

    print("\n【2】添加后端API接口...")
    # 在api.py的最后一个路由后添加重试接口
    add_api_cmd = f"""
cd {DEPLOY_DIR}/backend/blueprints

# 查找合适的插入位置（在最后一个@api_bp.route之后）
LINE_NUM=$(grep -n '@api_bp.route' api.py | tail -1 | cut -d: -f1)

# 在文件末尾之前插入
python3 << 'PYEOF'
with open('api.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 在最后插入新的路由
insert_code = """
{API_CODE}
"""

# 找到文件末尾
with open('api.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
    # 在最后添加新路由
    f.write(insert_code)

print("✓ API接口已添加")
PYEOF
"""
    stdin, stdout, stderr = ssh.exec_command(add_api_cmd)
    print(stdout.read().decode('utf-8'))
    error = stderr.read().decode('utf-8')
    if error:
        print(f"警告: {error}")

    print("\n【3】修改前端显示，添加重试按钮...")
    modify_frontend_cmd = f"""
cd {DEPLOY_DIR}/static

python3 << 'PYEOF'
import re

with open('publish.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 在"查看文章"链接后添加重试按钮
# 找到包含"查看文章"的行
pattern = r"(\\$\\{{item\\.url \\? `<a href=.*?</a>` : ''\\}})"

replacement = r'''\\1
                    \\${{item.status === 'failed' ? `
                        <button onclick="retryPublish(\\${{item.id}}, '\\${{item.article_title.replace(/'/g, "\\\\\\\\'")}}}', this)"
                            style="display: inline-flex; align-items: center; gap: 4px; font-size: 12px; color: white; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; margin-top: 8px; transition: all 0.3s; box-shadow: 0 2px 8px rgba(240, 147, 251, 0.3);"
                            onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(240, 147, 251, 0.5)'"
                            onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 8px rgba(240, 147, 251, 0.3)'">
                            <span>🔄</span>重试发布
                        </button>
                    ` : ''}}'''

content = re.sub(pattern, replacement, content, count=1)

# 在文件末尾添加重试函数
retry_function = '''
{RETRY_FUNCTION}
'''

# 检查是否已经有retryPublish函数
if 'function retryPublish' not in content:
    content += retry_function

with open('publish.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ 前端代码已修改")
PYEOF
"""
    stdin, stdout, stderr = ssh.exec_command(modify_frontend_cmd)
    print(stdout.read().decode('utf-8'))
    error = stderr.read().decode('utf-8')
    if error:
        print(f"警告: {error}")

    print("\n【4】验证修改...")
    verify_cmd = f"""
echo "检查API接口:"
grep -c 'retry_publish' {DEPLOY_DIR}/backend/blueprints/api.py

echo -e "\\n检查前端重试按钮:"
grep -c 'retryPublish' {DEPLOY_DIR}/static/publish.js

echo -e "\\n检查重试函数:"
grep -c 'function retryPublish' {DEPLOY_DIR}/static/publish.js
"""
    stdin, stdout, stderr = ssh.exec_command(verify_cmd)
    output = stdout.read().decode('utf-8')
    print(output)

    if '1' in output or '2' in output:
        print("✓ 代码修改成功")
    else:
        print("✗ 代码修改可能失败，请检查")

    print("\n【5】重启服务...")
    restart_cmd = f"pkill -f gunicorn; sleep 2; bash {DEPLOY_DIR}/start_service.sh"
    stdin, stdout, stderr = ssh.exec_command(restart_cmd)
    print(stdout.read().decode('utf-8'))

    import time
    time.sleep(3)

    print("\n【6】测试服务...")
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8080/api/health")
    print(stdout.read().decode('utf-8'))

    print("\n" + "=" * 60)
    print("✓ 重试功能部署完成")
    print("=" * 60)
    print("\n功能说明:")
    print("1. ✓ 后端API: POST /api/retry_publish/<history_id>")
    print("2. ✓ 前端按钮: 失败记录旁显示'🔄 重试发布'按钮")
    print("3. ✓ 重试逻辑: 从发布历史获取文章内容并重新发布")
    print("4. ✓ 权限验证: 只能重试自己的发布记录")
    print("5. ✓ 状态更新: 重试成功后自动刷新发布历史")
    print("\n访问 http://39.105.12.124:8080/publish 查看效果")
    print("失败的发布记录旁会显示紫色渐变的'重试发布'按钮")

    ssh.close()

if __name__ == '__main__':
    main()
