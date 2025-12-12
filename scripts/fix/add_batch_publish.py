#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加批量发布功能
"""
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

# 批量发布功能的JavaScript代码
BATCH_PUBLISH_JS = """

// 批量发布状态跟踪
let batchPublishInProgress = false;
let batchPublishResults = [];

// 批量发布所有文章
async function batchPublishAllArticles() {
    if (batchPublishInProgress) {
        alert('批量发布正在进行中，请稍候...');
        return;
    }

    if (!currentArticles || currentArticles.length === 0) {
        alert('没有可发布的文章');
        return;
    }

    // 获取已配置的知乎账号
    try {
        const accountsRes = await fetch('/api/accounts');
        const accountsData = await accountsRes.json();
        const accounts = accountsData.accounts || accountsData || [];
        const zhihuAccounts = accounts.filter(acc => acc.platform === '知乎' && acc.status === 'success');

        if (zhihuAccounts.length === 0) {
            alert('请先在账号配置中添加并登录知乎账号');
            return;
        }

        // 选择账号
        let selectedAccount;
        if (zhihuAccounts.length === 1) {
            selectedAccount = zhihuAccounts[0];
        } else {
            const accountList = zhihuAccounts.map((acc, i) => `${i+1}. ${acc.username}${acc.notes ? ' (' + acc.notes + ')' : ''}`).join('\\n');
            const choice = prompt(`请选择知乎账号用于批量发布:\\n\\n${accountList}\\n\\n输入序号 (1-${zhihuAccounts.length}):`);

            if (!choice || isNaN(choice) || choice < 1 || choice > zhihuAccounts.length) {
                return;
            }
            selectedAccount = zhihuAccounts[parseInt(choice) - 1];
        }

        // 确认批量发布
        const confirmMsg = `确认批量发布所有文章到知乎？\\n\\n共 ${currentArticles.length} 篇文章\\n账号: ${selectedAccount.username}\\n\\n所有文章将公开发布`;
        if (!confirm(confirmMsg)) {
            return;
        }

        // 开始批量发布
        batchPublishInProgress = true;
        batchPublishResults = [];

        // 更新批量发布按钮状态
        const batchBtn = document.getElementById('batch-publish-btn');
        if (batchBtn) {
            batchBtn.disabled = true;
            batchBtn.textContent = '⏳ 批量发布中...';
        }

        // 显示进度
        console.log(`开始批量发布 ${currentArticles.length} 篇文章...`);

        // 逐个发布文章（避免并发过多）
        for (let i = 0; i < currentArticles.length; i++) {
            const article = currentArticles[i];
            const statusEl = document.getElementById(`publish-status-${i}`);

            try {
                statusEl.innerHTML = `<span style="color: blue;">⏳ [${i+1}/${currentArticles.length}] 发布中...</span>`;

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
                    statusEl.innerHTML = `<span style="color: green;">✅ 发布成功！<a href="${url}" target="_blank" style="margin-left:5px;">查看</a></span>`;
                    batchPublishResults.push({ index: i, success: true, url: url });
                } else {
                    statusEl.innerHTML = `<span style="color: red;">❌ ${result.message || '发布失败'}</span>`;
                    batchPublishResults.push({ index: i, success: false, error: result.message });
                }

                // 发布间隔，避免频率过高
                if (i < currentArticles.length - 1) {
                    await new Promise(resolve => setTimeout(resolve, 3000)); // 等待3秒
                }

            } catch (error) {
                statusEl.innerHTML = `<span style="color: red;">❌ 错误: ${error.message}</span>`;
                batchPublishResults.push({ index: i, success: false, error: error.message });
            }
        }

        // 批量发布完成
        batchPublishInProgress = false;

        // 恢复按钮状态
        if (batchBtn) {
            batchBtn.disabled = false;
            batchBtn.textContent = '🚀 批量发布全部';
        }

        // 显示结果摘要
        const successCount = batchPublishResults.filter(r => r.success).length;
        const failCount = batchPublishResults.length - successCount;

        alert(`批量发布完成！\\n\\n成功: ${successCount} 篇\\n失败: ${failCount} 篇`);

        console.log('批量发布结果:', batchPublishResults);

    } catch (error) {
        batchPublishInProgress = false;
        alert(`批量发布出错: ${error.message}`);
        console.error('批量发布错误:', error);
    }
}
"""

# 批量发布按钮的CSS样式
BATCH_PUBLISH_CSS = """

/* 批量发布按钮 */
.batch-publish-section {
    margin-top: 20px;
    padding: 15px;
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    border-radius: 8px;
    text-align: center;
}

.btn-batch-publish {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    color: white !important;
    border: none;
    padding: 12px 24px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 16px;
    font-weight: 600;
    transition: all 0.3s;
    box-shadow: 0 4px 15px rgba(245, 87, 108, 0.3);
}

.btn-batch-publish:hover:not(:disabled) {
    transform: translateY(-3px);
    box-shadow: 0 6px 20px rgba(245, 87, 108, 0.5);
}

.btn-batch-publish:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.batch-publish-hint {
    margin-top: 10px;
    font-size: 14px;
    color: #666;
}
"""

try:
    print("=" * 80)
    print("添加批量发布功能")
    print("=" * 80)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
    print("✓ SSH连接成功\n")

    # 1. 添加JavaScript代码
    print("[1/4] 添加批量发布JavaScript代码...")
    cmd = f"cat >> /home/u_topn/TOP_N/static/app_upload.js << 'ENDJS'\n{BATCH_PUBLISH_JS}\nENDJS"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    stdout.read()
    print("✓ JavaScript代码已添加")

    # 2. 添加CSS样式
    print("\n[2/4] 添加批量发布CSS样式...")
    cmd = f"cat >> /home/u_topn/TOP_N/static/style.css << 'ENDCSS'\n{BATCH_PUBLISH_CSS}\nENDCSS"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    stdout.read()
    print("✓ CSS样式已添加")

    # 3. 修改HTML，添加批量发布按钮
    print("\n[3/4] 修改HTML，添加批量发布按钮...")

    # 在文章列表section的action-buttons之前添加批量发布按钮
    html_patch = """
            <!-- 批量发布区域 -->
            <div class="batch-publish-section">
                <button id="batch-publish-btn" class="btn btn-batch-publish" onclick="batchPublishAllArticles()">
                    🚀 批量发布全部
                </button>
                <p class="batch-publish-hint">将所有文章一次性发布到知乎（每篇间隔3秒）</p>
            </div>
"""

    # 使用sed在指定位置插入批量发布按钮 - 已注释，改用JavaScript动态注入
    # cmd = f"""sed -i '/<div class="action-buttons">/i\\...' /home/u_topn/TOP_N/templates/index.html"""

    # 简化方案：直接在文件末尾添加说明
    print("  提示：批量发布按钮已准备，需要在前端JavaScript中动态添加")

    # 创建动态添加按钮的JavaScript代码
    dynamic_button_js = """

// 动态添加批量发布按钮
function addBatchPublishButton() {
    const container = document.getElementById('articles-container');
    if (!container || container.querySelector('.batch-publish-section')) {
        return; // 已存在或容器不存在
    }

    const batchSection = document.createElement('div');
    batchSection.className = 'batch-publish-section';
    batchSection.innerHTML = `
        <button id="batch-publish-btn" class="btn btn-batch-publish" onclick="batchPublishAllArticles()">
            🚀 批量发布全部
        </button>
        <p class="batch-publish-hint">将所有文章一次性发布到知乎（每篇间隔3秒）</p>
    `;

    // 在文章容器之前插入
    container.parentNode.insertBefore(batchSection, container);
}

// 修改displayArticles函数，添加批量发布按钮
const originalDisplayArticlesFunc = displayArticles;
displayArticles = function(articles) {
    originalDisplayArticlesFunc(articles);

    // 添加批量发布按钮
    setTimeout(() => {
        addBatchPublishButton();
    }, 100);
};
"""

    cmd = f"cat >> /home/u_topn/TOP_N/static/app_upload.js << 'ENDJS'\n{dynamic_button_js}\nENDJS"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    stdout.read()
    print("✓ 动态添加按钮代码已添加")

    # 4. 重启服务
    print("\n[4/4] 重启服务...")
    cmd = "sudo systemctl restart topn"
    ssh.exec_command(cmd, timeout=30)

    import time
    time.sleep(4)

    # 检查服务状态
    cmd = "sudo systemctl status topn --no-pager | head -15"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    print(stdout.read().decode('utf-8'))

    print("\n" + "=" * 80)
    print("✅ 批量发布功能添加完成!")
    print("=" * 80)
    print("""
新功能说明:
✓ 在文章列表上方添加了"🚀 批量发布全部"按钮
✓ 点击后自动选择知乎账号
✓ 确认后逐个发布所有文章
✓ 每篇文章间隔3秒（避免频率过高）
✓ 实时显示每篇文章的发布状态
✓ 完成后显示成功/失败统计

使用方法:
1. 生成文章后，点击文章列表上方的"批量发布全部"按钮
2. 选择知乎账号
3. 确认批量发布
4. 等待所有文章发布完成
5. 查看发布结果统计

注意事项:
- 批量发布会逐个发布文章，需要一定时间
- 每篇文章间隔3秒，避免被知乎限流
- 发布过程中请勿关闭页面
- 可以实时查看每篇文章的发布状态
    """)

    ssh.close()

except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
