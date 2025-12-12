#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署文章一键发布功能
"""
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

# 修改后的displayArticles函数 - 添加发布按钮
DISPLAY_ARTICLES_FUNCTION = """
// 全局变量保存当前生成的文章
let currentArticles = [];

function displayArticles(articles) {
    currentArticles = articles; // 保存文章数据
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
                <button class="btn btn-small btn-publish" onclick="publishArticle(${index})">
                    🚀 发布到知乎
                </button>
                <span class="publish-status" id="status-${index}"></span>
            </div>
        `;
        container.appendChild(card);
    });
}

// 发布单篇文章
async function publishArticle(articleIndex) {
    const article = currentArticles[articleIndex];
    const statusEl = document.getElementById(`status-${articleIndex}`);

    // 检查是否有已配置的知乎账号
    const accounts = await fetch('/api/accounts').then(r => r.json());
    const zhihuAccounts = accounts.filter(acc => acc.platform === '知乎' && acc.status === 'success');

    if (zhihuAccounts.length === 0) {
        statusEl.innerHTML = '<span style="color: red;">❌ 未找到已登录的知乎账号，请先在账号配置中添加并测试知乎账号</span>';
        return;
    }

    // 如果只有一个账号，直接使用；否则弹出选择对话框
    let selectedAccount;
    if (zhihuAccounts.length === 1) {
        selectedAccount = zhihuAccounts[0];
    } else {
        // 显示账号选择对话框
        const accountOptions = zhihuAccounts.map(acc =>
            `<option value="${acc.username}">${acc.username} (${acc.notes || '无备注'})</option>`
        ).join('');

        const choice = prompt(`请选择知乎账号:\\n${zhihuAccounts.map((acc, i) => `${i+1}. ${acc.username}`).join('\\n')}\\n\\n输入序号(1-${zhihuAccounts.length}):`);

        if (!choice || isNaN(choice) || choice < 1 || choice > zhihuAccounts.length) {
            statusEl.innerHTML = '<span style="color: orange;">⚠️ 已取消发布</span>';
            return;
        }
        selectedAccount = zhihuAccounts[parseInt(choice) - 1];
    }

    // 确认发布
    const confirmMsg = `确认发布到知乎？\\n\\n标题: ${article.title}\\n账号: ${selectedAccount.username}\\n\\n发布后文章将公开可见`;
    if (!confirm(confirmMsg)) {
        statusEl.innerHTML = '<span style="color: orange;">⚠️ 已取消发布</span>';
        return;
    }

    // 开始发布
    statusEl.innerHTML = '<span style="color: blue;">⏳ 正在发布...</span>';

    try {
        const response = await fetch('/api/zhihu/post', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: selectedAccount.username,
                title: article.title,
                content: article.content,
                topics: [],
                draft: false  // 直接发布
            })
        });

        const result = await response.json();

        if (result.success) {
            statusEl.innerHTML = `<span style="color: green;">✅ 发布成功！<a href="${result.url}" target="_blank">查看文章</a></span>`;
        } else {
            statusEl.innerHTML = `<span style="color: red;">❌ 发布失败: ${result.message}</span>`;
        }
    } catch (error) {
        statusEl.innerHTML = `<span style="color: red;">❌ 发布失败: ${error.message}</span>`;
    }
}
"""

# CSS样式 - 添加发布按钮样式
PUBLISH_BUTTON_STYLES = """
.article-actions {
    margin-top: 15px;
    display: flex;
    align-items: center;
    gap: 10px;
}

.btn-publish {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 5px;
    cursor: pointer;
    font-size: 14px;
    transition: transform 0.2s;
}

.btn-publish:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.publish-status {
    font-size: 14px;
}

.publish-status a {
    color: #667eea;
    text-decoration: none;
    margin-left: 5px;
}

.publish-status a:hover {
    text-decoration: underline;
}
"""

try:
    print("=" * 80)
    print("部署文章一键发布功能")
    print("=" * 80)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
    print("✓ SSH连接成功\\n")

    # 1. 备份现有文件
    print("[1/4] 备份现有文件...")
    sftp = ssh.open_sftp()
    try:
        sftp.stat('/home/u_topn/TOP_N/static/app_upload.js.backup_publish')
    except:
        cmd = "cp /home/u_topn/TOP_N/static/app_upload.js /home/u_topn/TOP_N/static/app_upload.js.backup_publish"
        ssh.exec_command(cmd, timeout=10)
        print("✓ 已备份 app_upload.js")

    try:
        sftp.stat('/home/u_topn/TOP_N/static/style.css.backup_publish')
    except:
        cmd = "cp /home/u_topn/TOP_N/static/style.css /home/u_topn/TOP_N/static/style.css.backup_publish"
        ssh.exec_command(cmd, timeout=10)
        print("✓ 已备份 style.css")

    # 2. 修改JavaScript文件
    print("\\n[2/4] 修改JavaScript文件...")

    # 下载现有文件
    remote_js_path = '/home/u_topn/TOP_N/static/app_upload.js'
    local_js_path = 'D:/work/code/TOP_N/app_upload_temp.js'
    sftp.get(remote_js_path, local_js_path)

    # 读取内容
    with open(local_js_path, 'r', encoding='utf-8') as f:
        js_content = f.read()

    # 找到displayArticles函数并替换
    import re
    # 找到函数开始位置
    pattern = r'function displayArticles\\(articles\\) \\{[^}]+\\}(?:\\s*\\n)?'

    if 'function displayArticles(' in js_content:
        # 替换displayArticles函数
        js_content = re.sub(
            r'function displayArticles\\(articles\\) \\{[\\s\\S]*?^\\}',
            DISPLAY_ARTICLES_FUNCTION.strip(),
            js_content,
            flags=re.MULTILINE
        )
    else:
        # 如果没找到，追加到文件末尾
        js_content += '\\n\\n' + DISPLAY_ARTICLES_FUNCTION

    # 保存修改后的文件
    with open(local_js_path, 'w', encoding='utf-8') as f:
        f.write(js_content)

    # 上传回服务器
    sftp.put(local_js_path, remote_js_path)
    print("✓ JavaScript文件已更新")

    # 3. 修改CSS文件
    print("\\n[3/4] 修改CSS文件...")

    remote_css_path = '/home/u_topn/TOP_N/static/style.css'
    local_css_path = 'D:/work/code/TOP_N/style_temp.css'
    sftp.get(remote_css_path, local_css_path)

    with open(local_css_path, 'r', encoding='utf-8') as f:
        css_content = f.read()

    # 检查是否已经添加过样式
    if '.article-actions' not in css_content:
        css_content += '\\n\\n/* 文章发布按钮样式 */\\n' + PUBLISH_BUTTON_STYLES

    with open(local_css_path, 'w', encoding='utf-8') as f:
        f.write(css_content)

    sftp.put(local_css_path, remote_css_path)
    print("✓ CSS文件已更新")

    sftp.close()

    # 4. 重启服务
    print("\\n[4/4] 重启服务...")
    cmd = "sudo systemctl restart topn"
    ssh.exec_command(cmd, timeout=30)

    import time
    time.sleep(4)

    # 检查服务状态
    cmd = "sudo systemctl status topn --no-pager | head -15"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    print(stdout.read().decode('utf-8'))

    print("\\n" + "=" * 80)
    print("✅ 一键发布功能部署完成!")
    print("=" * 80)
    print("""
功能说明:
1. 每篇生成的文章现在都有"🚀 发布到知乎"按钮
2. 点击按钮后会自动选择已登录的知乎账号
3. 确认后自动发布文章到知乎
4. 发布状态会实时显示在按钮旁边
5. 发布成功后可直接点击链接查看文章

使用方法:
1. 访问 http://39.105.12.124:8080
2. 确保已在"账号配置"中添加知乎账号并完成扫码登录
3. 生成文章后，点击任意文章的"发布到知乎"按钮
4. 选择账号并确认发布

注意事项:
- 发布前请确保内容符合知乎社区规范
- 发布的文章将公开可见
- 建议先使用草稿模式测试（需修改draft参数）
    """)

    # 清理临时文件
    import os
    try:
        os.remove(local_js_path)
        os.remove(local_css_path)
    except:
        pass

    ssh.close()

except Exception as e:
    print(f"\\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
