#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署重试功能
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
    print("部署重试功能")
    print("=" * 60)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=10)

    print("\n【1】上传重试API代码...")
    # 使用sftp上传api_retry.py
    sftp = ssh.open_sftp()
    try:
        sftp.put('D:\\work\\code\\TOP_N\\backend\\blueprints\\api_retry.py',
                 f'{DEPLOY_DIR}/backend/blueprints/api_retry.py')
        print("✓ API代码已上传")
    finally:
        sftp.close()

    print("\n【2】将重试API添加到api.py...")
    add_api_cmd = f"""
cd {DEPLOY_DIR}/backend/blueprints

# 备份
cp api.py api.py.bak.retry

# 读取重试API代码
python3 << 'PYEOF'
# 读取api_retry.py的路由代码
with open('api_retry.py', 'r', encoding='utf-8') as f:
    retry_code = f.read()

# 只提取路由函数（去掉头部注释）
retry_code = retry_code.split('@api_bp.route', 1)[1] if '@api_bp.route' in retry_code else ''
retry_code = '@api_bp.route' + retry_code

# 读取api.py
with open('api.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 检查是否已经添加过
if 'retry_publish' in content:
    print('✓ 重试API已存在，跳过添加')
else:
    # 在文件末尾添加
    with open('api.py', 'a', encoding='utf-8') as f:
        f.write('\\n\\n')
        f.write(retry_code)
    print('✓ 重试API已添加到api.py')
PYEOF
"""
    stdin, stdout, stderr = ssh.exec_command(add_api_cmd)
    print(stdout.read().decode('utf-8'))
    error = stderr.read().decode('utf-8')
    if error and 'warning' not in error.lower():
        print(f"错误: {error}")

    print("\n【3】修改publish.js，添加重试按钮...")
    modify_js_cmd = f"""
cd {DEPLOY_DIR}/static

# 备份
cp publish.js publish.js.bak.retry

python3 << 'PYEOF'
with open('publish.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 在displayPublishHistory函数的表格行中添加重试按钮
# 找到"查看文章"链接那一行
import re

# 在"查看文章"之后添加重试按钮
pattern = r"(\\$\\{{item\\.url \\? `<a href=.*?</a>` : ''\\}})"

replacement = r'''\\1
                    \\${{item.status === 'failed' && item.article_id ? `
                        <button onclick="retryPublish(\\${{item.id}}, \\'\\${{item.article_title.replace(/'/g, "\\\\\\\\'")}}}\\', this)"
                            style="display: inline-flex; align-items: center; gap: 4px; font-size: 12px; color: white; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; margin-top: 8px; transition: all 0.3s; box-shadow: 0 2px 8px rgba(240, 147, 251, 0.3);"
                            onmouseover="this.style.transform=\\'translateY(-2px)\\'; this.style.boxShadow=\\'0 4px 12px rgba(240, 147, 251, 0.5)\\'"
                            onmouseout="this.style.transform=\\'translateY(0)\\'; this.style.boxShadow=\\'0 2px 8px rgba(240, 147, 251, 0.3)\\'">
                            <span>🔄</span>重试发布
                        </button>
                    ` : ''}}'''

if 'retryPublish' not in content:
    content = re.sub(pattern, replacement, content, count=1)

    # 在文件末尾添加重试函数
    retry_function = '''

// 重试发布失败的文章
async function retryPublish(historyId, articleTitle, button) {
    if (!confirm(`确定要重新发布《${{articleTitle}}》吗？`)) {
        return;
    }

    // 禁用按钮
    button.disabled = true;
    const originalHTML = button.innerHTML;
    button.innerHTML = '<span>⏳</span>重试中...';
    button.style.background = 'linear-gradient(135deg, #ccc 0%, #999 100%)';
    button.style.cursor = 'not-allowed';

    try {
        const response = await fetch(`/api/retry_publish/${{historyId}}`, {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/json'
            }}
        }});

        const data = await response.json();

        if (data.success) {
            alert(`重新发布成功！\\\\n${{data.message || ''}}`);
            // 刷新发布历史
            loadPublishHistory();
        } else {{
            alert(`重新发布失败：${{data.error || data.message || '未知错误'}}`);
            // 恢复按钮
            button.disabled = false;
            button.innerHTML = originalHTML;
            button.style.background = 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)';
            button.style.cursor = 'pointer';
        }}
    }} catch (error) {{
        alert('重新发布失败: ' + error.message);
        // 恢复按钮
        button.disabled = false;
        button.innerHTML = originalHTML;
        button.style.background = 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)';
        button.style.cursor = 'pointer';
    }}
}}
'''
    content += retry_function
    print('✓ 重试按钮和函数已添加')
else:
    print('✓ 重试功能已存在，跳过添加')

with open('publish.js', 'w', encoding='utf-8') as f:
    f.write(content)
PYEOF
"""
    stdin, stdout, stderr = ssh.exec_command(modify_js_cmd)
    print(stdout.read().decode('utf-8'))
    error = stderr.read().decode('utf-8')
    if error and 'warning' not in error.lower():
        print(f"错误: {error}")

    print("\n【4】验证修改...")
    verify_cmd = f"""
echo "检查API接口:"
grep -c 'def retry_publish' {DEPLOY_DIR}/backend/blueprints/api.py || echo "0"

echo -e "\\n检查前端重试按钮:"
grep -c 'retryPublish' {DEPLOY_DIR}/static/publish.js || echo "0"
"""
    stdin, stdout, stderr = ssh.exec_command(verify_cmd)
    output = stdout.read().decode('utf-8')
    print(output)

    print("\n【5】重启服务...")
    restart_cmd = f"pkill -f gunicorn && sleep 2 && bash {DEPLOY_DIR}/start_service.sh"
    stdin, stdout, stderr = ssh.exec_command(restart_cmd)
    time_out = stdout.read().decode('utf-8')
    print(time_out)

    import time
    time.sleep(3)

    print("\n【6】测试服务健康...")
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8080/api/health")
    print(stdout.read().decode('utf-8'))

    print("\n" + "=" * 60)
    print("✓ 重试功能部署完成")
    print("=" * 60)
    print("\n功能说明:")
    print("1. ✓ 失败记录旁显示'🔄 重试发布'按钮（紫色渐变）")
    print("2. ✓ 只有关联了文章的失败记录才显示重试按钮")
    print("3. ✓ 临时发布的失败记录不显示重试按钮")
    print("4. ✓ 点击重试会重新发布文章并更新历史记录")
    print("5. ✓ 重试成功后自动刷新发布历史")
    print("\n访问 http://39.105.12.124:8080/publish 查看效果")

    ssh.close()

if __name__ == '__main__':
    main()
