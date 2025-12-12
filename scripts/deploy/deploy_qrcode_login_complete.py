#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署完整的二维码扫码登录功能
"""
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

# Flask API代码片段 - 添加到app_with_upload.py
API_CODE = '''
# 二维码登录相关API
qr_login_sessions = {}  # 存储二维码登录会话

@app.route('/api/accounts/<int:account_id>/qrlogin', methods=['POST'])
def start_qr_login(account_id):
    """开始二维码登录"""
    try:
        accounts = load_accounts()
        account = next((acc for acc in accounts if acc.get('id') == account_id), None)

        if not account:
            return jsonify({'error': '账号不存在'}), 404

        username = account.get('username', '')

        # 导入二维码登录模块
        from qrcode_login import ZhihuQRCodeLogin

        # 创建登录会话
        session_id = str(account_id)
        qr_login = ZhihuQRCodeLogin(mode='drission')

        # 获取二维码
        result = qr_login.get_qrcode()

        if result['success']:
            # 保存会话
            qr_login_sessions[session_id] = qr_login

            return jsonify({
                'success': True,
                'session_id': session_id,
                'qrcode': result['qrcode_base64'],
                'message': '二维码获取成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': result.get('message', '获取二维码失败')
            }), 500

    except Exception as e:
        logger.error(f"Start QR login error: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/qrlogin/<session_id>/status', methods=['GET'])
def check_qr_status(session_id):
    """检查二维码登录状态"""
    try:
        qr_login = qr_login_sessions.get(session_id)

        if not qr_login:
            return jsonify({'success': False, 'status': 'expired', 'message': '会话不存在'})

        # 检查登录状态
        result = qr_login.check_login_status()

        return jsonify(result)

    except Exception as e:
        logger.error(f"Check QR status error: {e}", exc_info=True)
        return jsonify({'success': False, 'status': 'error', 'message': str(e)})

@app.route('/api/qrlogin/<session_id>/complete', methods=['POST'])
def complete_qr_login(session_id):
    """完成二维码登录并保存Cookie"""
    try:
        qr_login = qr_login_sessions.get(session_id)

        if not qr_login:
            return jsonify({'success': False, 'message': '会话不存在'})

        data = request.get_json() or {}
        username = data.get('username', session_id)

        # 保存Cookie
        result = qr_login.save_cookies(username)

        # 关闭浏览器
        qr_login.close()

        # 清理会话
        del qr_login_sessions[session_id]

        # 更新账号状态
        accounts = load_accounts()
        for acc in accounts:
            if str(acc.get('id')) == session_id or acc.get('username') == username:
                acc['status'] = 'success'
                acc['last_test'] = datetime.now().isoformat()
        save_accounts(accounts)

        return jsonify(result)

    except Exception as e:
        logger.error(f"Complete QR login error: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)})
'''

def main():
    try:
        print("="*80)
        print("部署完整二维码扫码登录功能")
        print("="*80)

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("✓ SSH连接成功\n")

        # 步骤1: 添加API到app_with_upload.py
        print("[1/3] 添加API接口...")
        cmd = f'''
cd /home/u_topn/TOP_N/backend

# 备份
cp app_with_upload.py app_with_upload.py.backup_qrcode

# 在文件末尾添加API代码（在if __name__ == '__main__'之前）
python3 << 'PYEOF'
with open('app_with_upload.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 查找插入位置
insert_marker = "if __name__ == '__main__':"
if insert_marker in content:
    parts = content.split(insert_marker)
    new_content = parts[0] + {repr(API_CODE)} + "\\n" + insert_marker + parts[1]

    with open('app_with_upload.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("✓ API代码已添加")
else:
    print("✗ 未找到插入位置")
PYEOF
'''
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=20)
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        print(output)
        if error:
            print(f"错误: {error}")

        # 步骤2: 重启服务
        print("\n[2/3] 重启服务...")
        cmd = "sudo systemctl restart topn && sleep 3"
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
        import time
        time.sleep(4)

        cmd = "sudo systemctl status topn --no-pager | head -15"
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        print(stdout.read().decode('utf-8'))

        # 步骤3: 提示前端修改
        print("\n[3/3] 前端修改说明...")
        print("""
================================================================================
✅ 后端API已部署！

新增API接口:
1. POST /api/accounts/<id>/qrlogin  - 开始二维码登录
2. GET  /api/qrlogin/<session_id>/status - 检查扫码状态
3. POST /api/qrlogin/<session_id>/complete - 完成登录保存Cookie

前端需要添加的代码（在account_config.js中）:

// 点击测试账号时调用
async function testAccountWithQR(accountId) {
    // 1. 获取二维码
    const response = await fetch(`/api/accounts/${accountId}/qrlogin`, {method: 'POST'});
    const data = await response.json();

    if (data.success) {
        // 2. 显示二维码
        showQRCodeModal(data.qrcode, data.session_id);

        // 3. 轮询检查状态
        pollQRStatus(data.session_id);
    }
}

function showQRCodeModal(qrcodeBase64, sessionId) {
    // 创建弹窗显示二维码
    const modal = document.createElement('div');
    modal.innerHTML = `
        <div style="position:fixed; top:50%; left:50%; transform:translate(-50%,-50%);
                    background:white; padding:30px; border-radius:10px; box-shadow:0 4px 20px rgba(0,0,0,0.3);
                    z-index:1000; text-align:center;">
            <h3>请使用知乎App扫码登录</h3>
            <img src="data:image/png;base64,${qrcodeBase64}" style="max-width:300px; margin:20px 0;">
            <p id="qr-status">等待扫码...</p>
            <button onclick="closeQRModal()">取消</button>
        </div>
        <div style="position:fixed; top:0; left:0; width:100%; height:100%;
                    background:rgba(0,0,0,0.5); z-index:999;" onclick="closeQRModal()"></div>
    `;
    modal.id = 'qr-modal';
    document.body.appendChild(modal);
    window.currentQRSession = sessionId;
}

async function pollQRStatus(sessionId) {
    const interval = setInterval(async () => {
        const response = await fetch(`/api/qrlogin/${sessionId}/status`);
        const data = await response.json();

        const statusEl = document.getElementById('qr-status');
        if (!statusEl) {
            clearInterval(interval);
            return;
        }

        if (data.status === 'scanned') {
            statusEl.textContent = '已扫描，请在手机上确认登录';
        } else if (data.status === 'success') {
            statusEl.textContent = '登录成功！';

            // 完成登录
            await fetch(`/api/qrlogin/${sessionId}/complete`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username: sessionId})
            });

            clearInterval(interval);
            setTimeout(() => {
                closeQRModal();
                loadAccounts(); // 刷新账号列表
                alert('登录成功！Cookie已保存');
            }, 1500);
        } else if (data.status === 'expired') {
            statusEl.textContent = '二维码已过期';
            clearInterval(interval);
        }
    }, 2000); // 每2秒检查一次
}

function closeQRModal() {
    const modal = document.getElementById('qr-modal');
    if (modal) modal.remove();
}

================================================================================
        """)

        print("\n" + "="*80)
        print("✅ 部署完成！")
        print("="*80)
        print("\n下一步: 修改前端页面添加上述代码")

        ssh.close()
        return True

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()
