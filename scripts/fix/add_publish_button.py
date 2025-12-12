#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为文章卡片添加发布按钮
"""
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

try:
    print("=" * 80)
    print("添加文章发布按钮功能")
    print("=" * 80)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
    print("✓ SSH连接成功\n")

    # 1. 备份文件
    print("[1/4] 备份文件...")
    cmd = "cd /home/u_topn/TOP_N/static && cp app_upload.js app_upload.js.backup_publish 2>/dev/null || true"
    ssh.exec_command(cmd, timeout=10)
    cmd = "cd /home/u_topn/TOP_N/static && cp style.css style.css.backup_publish 2>/dev/null || true"
    ssh.exec_command(cmd, timeout=10)
    print("✓ 备份完成")

    # 2. 添加发布功能JavaScript代码
    print("\n[2/4] 添加JavaScript代码...")

    js_code = """

// === 文章发布功能 ===
let currentArticles = [];

// 重写displayArticles函数以添加发布按钮
const originalDisplayArticles = displayArticles;
displayArticles = function(articles) {
    currentArticles = articles;
    const container = document.getElementById('articles-container');
    container.innerHTML = '';

    articles.forEach((article, index) => {
        const card = document.createElement('div');
        card.className = 'article-card';
        card.innerHTML = `
            <span class="article-type">${article.type}</span>
            <h3>${article.title}</h3>
            <div class="article-content">${article.content}</div>
            <div class="article-actions">
                <button class="btn btn-small btn-publish" onclick="publishArticleToZhihu(${index})">
                    🚀 发布到知乎
                </button>
                <span class="publish-status" id="publish-status-${index}"></span>
            </div>
        `;
        container.appendChild(card);
    });
};

// 发布文章到知乎
async function publishArticleToZhihu(articleIndex) {
    const article = currentArticles[articleIndex];
    const statusEl = document.getElementById(`publish-status-${articleIndex}`);

    try {
        // 获取已配置的知乎账号
        statusEl.innerHTML = '<span style="color: blue;">⏳ 检查账号...</span>';
        const accountsRes = await fetch('/api/accounts');
        const accounts = await accountsRes.json();
        const zhihuAccounts = accounts.filter(acc => acc.platform === '知乎' && acc.status === 'success');

        if (zhihuAccounts.length === 0) {
            statusEl.innerHTML = '<span style="color: red;">❌ 请先在账号配置中添加并登录知乎账号</span>';
            return;
        }

        // 选择账号
        let selectedAccount;
        if (zhihuAccounts.length === 1) {
            selectedAccount = zhihuAccounts[0];
        } else {
            const accountList = zhihuAccounts.map((acc, i) => `${i+1}. ${acc.username}${acc.notes ? ' (' + acc.notes + ')' : ''}`).join('\\n');
            const choice = prompt(`请选择知乎账号:\\n\\n${accountList}\\n\\n输入序号 (1-${zhihuAccounts.length}):`);

            if (!choice || isNaN(choice) || choice < 1 || choice > zhihuAccounts.length) {
                statusEl.innerHTML = '<span style="color: orange;">⚠️ 已取消</span>';
                return;
            }
            selectedAccount = zhihuAccounts[parseInt(choice) - 1];
        }

        // 确认发布
        if (!confirm(`确认发布到知乎？\\n\\n标题: ${article.title}\\n账号: ${selectedAccount.username}\\n\\n文章将公开发布`)) {
            statusEl.innerHTML = '<span style="color: orange;">⚠️ 已取消</span>';
            return;
        }

        // 开始发布
        statusEl.innerHTML = '<span style="color: blue;">⏳ 正在发布...</span>';

        const response = await fetch('/api/zhihu/post', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                username: selectedAccount.username,
                title: article.title,
                content: article.content,
                topics: [],
                draft: false
            })
        });

        const result = await response.json();

        if (result.success) {
            const url = result.url || '#';
            statusEl.innerHTML = `<span style="color: green;">✅ 发布成功！<a href="${url}" target="_blank" style="margin-left:5px;">查看文章</a></span>`;
        } else {
            statusEl.innerHTML = `<span style="color: red;">❌ ${result.message || '发布失败'}</span>`;
        }
    } catch (error) {
        statusEl.innerHTML = `<span style="color: red;">❌ 错误: ${error.message}</span>`;
    }
}
"""

    cmd = f"cat >> /home/u_topn/TOP_N/static/app_upload.js << 'ENDJS'\n{js_code}\nENDJS"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    stdout.read()
    print("✓ JavaScript代码已添加")

    # 3. 添加CSS样式
    print("\n[3/4] 添加CSS样式...")

    css_code = """

/* 文章发布按钮样式 */
.article-actions {
    margin-top: 15px;
    padding-top: 15px;
    border-top: 1px solid #e0e0e0;
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
}

.btn-publish {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white !important;
    border: none;
    padding: 8px 16px;
    border-radius: 5px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.3s;
}

.btn-publish:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.publish-status {
    font-size: 14px;
    flex: 1;
}

.publish-status a {
    color: #667eea;
    text-decoration: none;
    font-weight: 500;
}

.publish-status a:hover {
    text-decoration: underline;
}
"""

    cmd = f"cat >> /home/u_topn/TOP_N/static/style.css << 'ENDCSS'\n{css_code}\nENDCSS"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    stdout.read()
    print("✓ CSS样式已添加")

    # 4. 重启服务
    print("\n[4/4] 重启服务...")
    cmd = "sudo systemctl restart topn"
    ssh.exec_command(cmd, timeout=30)

    import time
    time.sleep(4)

    # 检查服务状态
    cmd = "sudo systemctl status topn --no-pager | head -15"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    output = stdout.read().decode('utf-8')
    print(output)

    print("\n" + "=" * 80)
    print("✅ 发布按钮添加完成!")
    print("=" * 80)
    print("""
功能说明:
✓ 每篇文章现在都有"🚀 发布到知乎"按钮
✓ 点击后自动选择已登录的知乎账号
✓ 确认后一键发布文章到知乎
✓ 实时显示发布状态
✓ 发布成功后可点击链接查看文章

使用步骤:
1. 访问 http://39.105.12.124:8080
2. 在"账号配置"中添加知乎账号并扫码登录
3. 生成文章后，点击"发布到知乎"按钮
4. 选择账号并确认，即可自动发布

注意:
- 发布的文章将公开可见
- 请确保内容符合知乎社区规范
    """)

    ssh.close()

except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
