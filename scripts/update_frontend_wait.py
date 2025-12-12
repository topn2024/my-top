#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新前端使用wait端点（阻塞式等待）
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
    print("更新前端使用wait端点...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=10)

    # 读取当前的publish.js
    stdin, stdout, stderr = ssh.exec_command(f"cat {DEPLOY_DIR}/static/publish.js")
    content = stdout.read().decode('utf-8')

    # 定义要替换的旧代码（轮询方式）
    old_code = '''// 轮询检查登录状态
let qrLoginPollingInterval = null;

function startQRLoginPolling(sessionId, article, modal) {
    let pollCount = 0;
    const maxPolls = 60; // 最多轮询60次 (2分钟)

    qrLoginPollingInterval = setInterval(async () => {
        pollCount++;

        if (pollCount > maxPolls) {
            stopQRLoginPolling();
            document.getElementById('qr-login-status').textContent = '登录超时，请重试';
            document.getElementById('qr-login-status').style.color = '#ef4444';
            return;
        }

        try {
            const response = await fetch('/api/zhihu/qr_login/check', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ session_id: sessionId })
            });

            const data = await response.json();

            if (data.success && data.logged_in) {
                // 登录成功
                stopQRLoginPolling();
                document.getElementById('qr-login-status').textContent = '✓ 登录成功！正在发布...';
                document.getElementById('qr-login-status').style.color = '#10b981';

                // 等待1秒后关闭弹窗并重新发布
                setTimeout(async () => {
                    document.body.removeChild(modal);
                    // 重新发布文章
                    await publishToZhihu(article);
                }, 1000);
            }

        } catch (error) {
            console.error('检查登录状态失败:', error);
        }

    }, 2000); // 每2秒检查一次
}

function stopQRLoginPolling() {
    if (qrLoginPollingInterval) {
        clearInterval(qrLoginPollingInterval);
        qrLoginPollingInterval = null;
    }
}'''

    # 定义新代码（使用wait端点）
    new_code = '''// 等待登录完成（使用wait端点，阻塞式）
async function startQRLoginPolling(sessionId, article, modal) {
    const statusElement = document.getElementById('qr-login-status');

    try {
        statusElement.textContent = '等待扫码登录...';
        statusElement.style.color = '#3b82f6';

        // 调用wait端点（会阻塞直到登录成功或超时）
        const response = await fetch('/api/zhihu/qr_login/wait', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId,
                timeout: 120  // 120秒超时
            })
        });

        const data = await response.json();

        if (data.success && data.logged_in) {
            // 登录成功
            statusElement.textContent = '✓ 登录成功！正在发布...';
            statusElement.style.color = '#10b981';

            // 等待1秒让用户看到成功提示
            await new Promise(resolve => setTimeout(resolve, 1000));

            // 关闭弹窗
            document.body.removeChild(modal);

            // 重新发布文章
            await publishToZhihu(article);
        } else {
            // 登录失败或超时
            statusElement.textContent = '✗ ' + (data.message || '登录失败');
            statusElement.style.color = '#ef4444';

            await new Promise(resolve => setTimeout(resolve, 2000));
            document.body.removeChild(modal);

            alert('登录失败：' + (data.message || '未知错误'));
        }

    } catch (error) {
        console.error('等待登录失败:', error);
        statusElement.textContent = '✗ 登录出错';
        statusElement.style.color = '#ef4444';

        await new Promise(resolve => setTimeout(resolve, 1000));
        document.body.removeChild(modal);

        alert('登录失败: ' + error.message);
    }
}

function stopQRLoginPolling() {
    // 不再需要，但保留以避免错误
}'''

    # 替换代码
    if old_code in content:
        new_content = content.replace(old_code, new_code)

        # 上传新内容
        print("✓ 找到需要替换的代码")
        stdin, stdout, stderr = ssh.exec_command(
            f"cat > {DEPLOY_DIR}/static/publish.js << 'EOFFILE'\n{new_content}\nEOFFILE"
        )
        stdout.read()
        print("✓ 前端代码已更新")
    else:
        print("⚠ 未找到需要替换的代码，可能已经更新过了")

    print("\n✓ 更新完成")
    print("\n改进内容:")
    print("1. 从轮询方式改为阻塞式等待（使用/api/zhihu/qr_login/wait端点）")
    print("2. 减少服务器负载（不再每2秒轮询一次）")
    print("3. 更快响应登录成功事件")

    ssh.close()

if __name__ == '__main__':
    main()
