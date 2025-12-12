#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复发布功能的API调用问题
"""
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

# 修复后的JavaScript代码
FIXED_PUBLISH_FUNCTION = """
// 发布文章到知乎
async function publishArticleToZhihu(articleIndex) {
    const article = currentArticles[articleIndex];
    const statusEl = document.getElementById(`publish-status-${articleIndex}`);

    try {
        // 获取已配置的知乎账号
        statusEl.innerHTML = '<span style="color: blue;">⏳ 检查账号...</span>';
        const accountsRes = await fetch('/api/accounts');
        const accountsData = await accountsRes.json();

        // 修复：正确获取accounts数组
        const accounts = accountsData.accounts || accountsData || [];
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
        console.error('发布错误:', error);
    }
}
"""

try:
    print("=" * 80)
    print("修复发布功能API调用")
    print("=" * 80)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
    print("✓ SSH连接成功\n")

    # 读取当前JavaScript文件
    print("[1/3] 读取当前JavaScript文件...")
    sftp = ssh.open_sftp()
    remote_file = '/home/u_topn/TOP_N/static/app_upload.js'
    local_file = 'D:/work/code/TOP_N/app_upload_temp_fix.js'

    sftp.get(remote_file, local_file)

    with open(local_file, 'r', encoding='utf-8') as f:
        js_content = f.read()

    print("✓ 文件已读取")

    # 替换publishArticleToZhihu函数
    print("\n[2/3] 替换发布函数...")

    import re
    # 找到并替换整个publishArticleToZhihu函数
    pattern = r'async function publishArticleToZhihu\(articleIndex\) \{[^}]*(?:\{[^}]*\}[^}]*)*\}'

    if 'publishArticleToZhihu' in js_content:
        # 使用更精确的匹配
        start_marker = 'async function publishArticleToZhihu(articleIndex) {'
        if start_marker in js_content:
            start_idx = js_content.find(start_marker)
            # 找到匹配的结束大括号
            brace_count = 0
            i = start_idx + len(start_marker) - 1
            while i < len(js_content):
                if js_content[i] == '{':
                    brace_count += 1
                elif js_content[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break
                i += 1

            # 替换函数
            js_content = js_content[:start_idx] + FIXED_PUBLISH_FUNCTION.strip() + js_content[end_idx:]
            print("✓ 函数已替换")
        else:
            print("⚠️ 未找到函数，将追加到文件末尾")
            js_content += '\n\n' + FIXED_PUBLISH_FUNCTION
    else:
        print("⚠️ 未找到函数，将追加到文件末尾")
        js_content += '\n\n' + FIXED_PUBLISH_FUNCTION

    # 保存并上传
    with open(local_file, 'w', encoding='utf-8') as f:
        f.write(js_content)

    sftp.put(local_file, remote_file)
    sftp.close()

    print("✓ 文件已更新")

    # 重启服务
    print("\n[3/3] 重启服务...")
    cmd = "sudo systemctl restart topn"
    ssh.exec_command(cmd, timeout=30)

    import time
    time.sleep(4)

    # 检查服务状态
    cmd = "sudo systemctl status topn --no-pager | head -15"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    print(stdout.read().decode('utf-8'))

    print("\n" + "=" * 80)
    print("✅ 修复完成!")
    print("=" * 80)
    print("""
修复内容:
- 修正了API响应数据的解析方式
- 添加了 const accounts = accountsData.accounts || accountsData || [];
- 确保正确获取accounts数组
- 添加了错误日志输出

现在可以重新测试发布功能了！
    """)

    # 清理临时文件
    import os
    try:
        os.remove(local_file)
    except:
        pass

    ssh.close()

except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
