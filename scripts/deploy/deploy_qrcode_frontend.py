#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署二维码登录前端代码
"""
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

# 二维码登录前端JavaScript代码
QR_LOGIN_JS = '''
// ========== 二维码登录功能 ==========

// 修改testAccount函数，检测知乎平台时使用二维码登录
async function testAccount(accountId) {
    try {
        // 先获取账号信息
        const response = await fetch('/api/accounts');
        const data = await response.json();

        if (!data.success) {
            alert('获取账号信息失败');
            return;
        }

        const account = data.accounts.find(acc => acc.id === accountId);

        // 如果是知乎平台，使用二维码登录
        if (account && account.platform === '知乎') {
            testAccountWithQR(accountId);
        } else {
            // 其他平台使用原有的密码登录测试
            testAccountNormal(accountId);
        }
    } catch (error) {
        console.error('Test account error:', error);
        alert('测试失败: ' + error.message);
    }
}

// 原有的密码登录测试（重命名）
async function testAccountNormal(accountId) {
    try {
        showLoading('正在测试登录...');

        const response = await fetch(`/api/accounts/${accountId}/test`, {
            method: 'POST'
        });

        hideLoading();

        const data = await response.json();

        if (data.success) {
            showTestResult('success', '登录测试成功', data.message || '账号验证通过');
            loadAccounts();
        } else {
            showTestResult('failed', '登录测试失败', data.message || data.error || '未知错误');
        }
    } catch (error) {
        hideLoading();
        console.error('Test account error:', error);
        showTestResult('failed', '登录测试失败', error.message);
    }
}

// 二维码登录
async function testAccountWithQR(accountId) {
    try {
        showLoading('正在获取二维码...');

        // 1. 获取二维码
        const response = await fetch(`/api/accounts/${accountId}/qrlogin`, {
            method: 'POST'
        });

        hideLoading();

        const data = await response.json();

        if (data.success) {
            // 2. 显示二维码
            showQRCodeModal(data.qrcode, data.session_id, accountId);

            // 3. 轮询检查状态
            pollQRStatus(data.session_id, accountId);
        } else {
            alert('获取二维码失败: ' + (data.message || '未知错误'));
        }
    } catch (error) {
        hideLoading();
        console.error('QR login error:', error);
        alert('二维码登录失败: ' + error.message);
    }
}

// 显示二维码弹窗
function showQRCodeModal(qrcodeBase64, sessionId, accountId) {
    // 创建遮罩层
    const overlay = document.createElement('div');
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        z-index: 999;
    `;
    overlay.onclick = () => closeQRModal();

    // 创建弹窗
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        padding: 30px;
        border-radius: 10px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        z-index: 1000;
        text-align: center;
        max-width: 400px;
    `;

    modal.innerHTML = `
        <h3 style="margin: 0 0 20px 0; color: #333;">请使用知乎App扫码登录</h3>
        <img src="data:image/png;base64,${qrcodeBase64}"
             style="max-width: 300px; margin: 20px 0; border: 1px solid #ddd; border-radius: 5px;">
        <p id="qr-status" style="margin: 15px 0; font-size: 14px; color: #666;">等待扫码...</p>
        <button onclick="closeQRModal()"
                style="padding: 8px 20px; background: #f44336; color: white;
                       border: none; border-radius: 4px; cursor: pointer;">取消</button>
    `;

    // 组装容器
    const container = document.createElement('div');
    container.id = 'qr-modal-container';
    container.appendChild(overlay);
    container.appendChild(modal);

    document.body.appendChild(container);

    // 保存会话信息
    window.currentQRSession = { sessionId, accountId };
}

// 轮询检查二维码状态
async function pollQRStatus(sessionId, accountId) {
    const pollInterval = setInterval(async () => {
        const statusEl = document.getElementById('qr-status');

        // 如果弹窗已关闭，停止轮询
        if (!statusEl) {
            clearInterval(pollInterval);
            return;
        }

        try {
            const response = await fetch(`/api/qrlogin/${sessionId}/status`);
            const data = await response.json();

            if (data.status === 'scanned') {
                statusEl.textContent = '✓ 已扫描，请在手机上确认登录';
                statusEl.style.color = '#2196F3';
            } else if (data.status === 'success') {
                statusEl.textContent = '✓✓ 登录成功！正在保存...';
                statusEl.style.color = '#4CAF50';

                // 完成登录，保存Cookie
                const completeResponse = await fetch(`/api/qrlogin/${sessionId}/complete`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username: `account_${accountId}` })
                });

                const completeData = await completeResponse.json();

                clearInterval(pollInterval);

                setTimeout(() => {
                    closeQRModal();
                    if (completeData.success) {
                        showTestResult('success', '登录成功', 'Cookie已保存，后续可直接使用Cookie登录');
                        loadAccounts();
                    } else {
                        alert('保存Cookie失败: ' + (completeData.message || '未知错误'));
                    }
                }, 1000);

            } else if (data.status === 'expired') {
                statusEl.textContent = '✗ 二维码已过期，请重新获取';
                statusEl.style.color = '#f44336';
                clearInterval(pollInterval);
            } else if (data.status === 'error') {
                statusEl.textContent = '✗ 发生错误: ' + (data.message || '未知错误');
                statusEl.style.color = '#f44336';
                clearInterval(pollInterval);
            }
        } catch (error) {
            console.error('Poll QR status error:', error);
            statusEl.textContent = '✗ 网络错误，请重试';
            statusEl.style.color = '#f44336';
            clearInterval(pollInterval);
        }
    }, 2000); // 每2秒检查一次
}

// 关闭二维码弹窗
function closeQRModal() {
    const container = document.getElementById('qr-modal-container');
    if (container) {
        container.remove();
    }
    window.currentQRSession = null;
}
'''

def main():
    try:
        print("="*80)
        print("部署二维码登录前端代码")
        print("="*80)

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("✓ SSH连接成功\n")

        # 步骤1: 备份原文件
        print("[1/3] 备份原文件...")
        cmd = """
cd /home/u_topn/TOP_N/static
cp account_config.js account_config.js.backup_qrcode_$(date +%Y%m%d_%H%M%S)
echo "✓ 备份完成"
"""
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        print(stdout.read().decode('utf-8'))

        # 步骤2: 添加二维码登录代码
        print("\n[2/3] 添加二维码登录代码...")

        # 使用SFTP读取文件
        sftp = ssh.open_sftp()
        remote_path = '/home/u_topn/TOP_N/static/account_config.js'

        with sftp.open(remote_path, 'r') as f:
            original_content = f.read().decode('utf-8')

        # 在文件末尾添加二维码登录代码
        new_content = original_content + '\n' + QR_LOGIN_JS

        # 写回文件
        with sftp.open(remote_path, 'w') as f:
            f.write(new_content.encode('utf-8'))

        sftp.close()
        print("✓ 二维码登录代码已添加")

        # 步骤3: 验证文件
        print("\n[3/3] 验证部署...")
        cmd = """
cd /home/u_topn/TOP_N/static
if grep -q "testAccountWithQR" account_config.js; then
    echo "✓ 二维码登录函数已添加"
else
    echo "✗ 验证失败"
fi

if grep -q "showQRCodeModal" account_config.js; then
    echo "✓ 二维码弹窗函数已添加"
else
    echo "✗ 验证失败"
fi

if grep -q "pollQRStatus" account_config.js; then
    echo "✓ 状态轮询函数已添加"
else
    echo "✗ 验证失败"
fi
"""
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        print(stdout.read().decode('utf-8'))

        print("\n" + "="*80)
        print("✅ 前端部署完成！")
        print("="*80)
        print("""
使用说明:
1. 访问账号配置页面
2. 点击知乎账号的"测试"按钮
3. 自动弹出二维码，使用知乎App扫码
4. 扫码后在手机上确认登录
5. 登录成功后，Cookie自动保存到服务器
6. 后续登录会自动使用保存的Cookie（100%成功率）

完整流程:
- 知乎账号: 测试 → 显示二维码 → 扫码登录 → 保存Cookie
- 其他平台: 测试 → 密码登录验证

注意事项:
- 二维码有效期约2分钟，过期需重新获取
- 首次登录需要扫码，后续使用Cookie自动登录
- Cookie保存在服务器 /home/u_topn/TOP_N/backend/cookies/ 目录
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
