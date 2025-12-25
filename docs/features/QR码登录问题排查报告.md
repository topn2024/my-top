# QR码登录问题排查报告

## 问题描述
用户在测试知乎账号登录时,报错:
```
二维码登录失败: Unexpected token '<', "<!doctype "... is not valid JSON
```

## 问题分析

### 错误原因
前端JavaScript调用的API端点与后端实际提供的API端点**不匹配**,导致前端收到HTML 404页面而不是JSON响应。

### 完整流程分析

#### 1. 前端代码 (`static/account_config.js`)
前端尝试调用以下端点:

```javascript
// 获取二维码
const response = await fetch(`/api/accounts/${accountId}/qrlogin`, {
    method: 'POST'
});

// 轮询状态
const response = await fetch(`/api/qrlogin/${sessionId}/status`);
```

**期望的端点:**
- `POST /api/accounts/<id>/qrlogin` - 获取二维码
- `GET /api/qrlogin/<session_id>/status` - 检查登录状态

#### 2. 后端实际端点 (`backend/app_with_upload.py`)
根据现有CSDN微信登录的实现模式,实际端点应该是:

```python
# app_with_upload.py中已有的模式:
@app.route('/api/qrcode/get_qr', methods=['POST'])
@app.route('/api/qrcode/check_status', methods=['POST'])
```

#### 3. 后端模块 (`backend/qrcode_login.py`)
该模块提供了完整的知乎二维码登录功能:
- `get_qrcode()` - 提取二维码 (line 36)
- `check_login_status()` - 轮询检测登录状态 (line 100+)

但缺少Flask路由注册!

## 问题根源

**根本原因**: `qrcode_login.py` 模块虽然实现了完整功能,但**没有在Flask应用中注册路由**。

对比已成功的CSDN微信登录实现 (`csdn_wechat_login.py`):

```python
# csdn_wechat_login.py - 成功案例
csdn_wechat_bp = Blueprint('csdn_wechat', __name__)

@csdn_wechat_bp.route('/api/csdn/wechat_qr', methods=['POST'])
def get_csdn_wechat_qr():
    # ...

@csdn_wechat_bp.route('/api/csdn/wechat_login_status', methods=['POST'])
def check_csdn_wechat_login_status():
    # ...

# app_with_upload.py中注册:
app.register_blueprint(csdn_wechat_bp)
```

而`qrcode_login.py`缺少:
1. ✗ 没有创建Blueprint
2. ✗ 没有定义Flask路由
3. ✗ 没有在app_with_upload.py中注册

## 解决方案

### 方案1: 重构qrcode_login.py为Blueprint (推荐)

参考`csdn_wechat_login.py`的完整实现,需要:

1. **修改 `backend/qrcode_login.py`**:
   - 创建Blueprint: `zhihu_qrcode_bp = Blueprint('zhihu_qrcode', __name__)`
   - 添加路由装饰器
   - 适配前端调用的端点名称

2. **修改 `backend/app_with_upload.py`**:
   ```python
   from qrcode_login import zhihu_qrcode_bp
   app.register_blueprint(zhihu_qrcode_bp)
   ```

3. **修改前端 `static/account_config.js`**:
   调整端点路径与后端保持一致

### 方案2: 在app_with_upload.py中直接添加路由

直接在`app_with_upload.py`中导入`qrcode_login.py`的类并添加路由:

```python
from qrcode_login import ZhihuQRLogin

@app.route('/api/accounts/<int:account_id>/qrlogin', methods=['POST'])
@login_required
def zhihu_qr_login(account_id):
    user = get_current_user()
    # 获取账号信息
    account = get_account_by_id(account_id, user.id)

    # 创建登录实例
    qr_login = ZhihuQRLogin()
    success, qrcode_base64 = qr_login.get_qrcode()

    if success:
        # 生成session_id
        session_id = f"{user.id}_{account_id}_{int(time.time())}"
        # 保存到全局字典
        qr_sessions[session_id] = {
            'login': qr_login,
            'account_id': account_id,
            'username': account.username
        }

        return jsonify({
            'success': True,
            'qrcode': qrcode_base64,
            'session_id': session_id
        })
    else:
        return jsonify({
            'success': False,
            'message': '获取二维码失败'
        }), 500

@app.route('/api/qrlogin/<session_id>/status', methods=['GET'])
@login_required
def check_qr_status(session_id):
    if session_id not in qr_sessions:
        return jsonify({'status': 'invalid'}), 404

    session_data = qr_sessions[session_id]
    qr_login = session_data['login']

    # 检查登录状态(非阻塞)
    status = qr_login.check_login_status(max_wait=1)

    if status == 'success':
        # 保存Cookie
        cookies = qr_login.get_cookies()
        save_cookies(session_data['username'], cookies)

        # 更新数据库状态
        update_account_status(session_data['account_id'], 'success')

        # 清理会话
        qr_login.close()
        del qr_sessions[session_id]

        return jsonify({'status': 'success'})
    elif status == 'scanned':
        return jsonify({'status': 'scanned'})
    else:
        return jsonify({'status': 'waiting'})
```

## 现有成功案例参考

### CSDN微信扫码登录 (`backend/csdn_wechat_login.py`)

**文件**: 485行完整实现

**特点**:
- ✅ 使用Blueprint架构
- ✅ 完整的会话管理 (`_login_sessions`)
- ✅ 前后端API对接正确
- ✅ 在`app_with_upload.py`中已注册

**核心API端点**:
```
POST /api/csdn/wechat_qr          - 获取二维码
POST /api/csdn/wechat_login_status - 检查登录状态
POST /api/csdn/cancel_wechat_login - 取消登录
```

**会话清理**: 自动清理30分钟过期会话

### 知乎二维码登录 (`backend/qrcode_login.py`)

**文件**: 实现完整但未集成

**已实现功能**:
- ✅ `ZhihuQRLogin` 类
- ✅ `get_qrcode()` - 二维码提取
- ✅ `check_login_status()` - 状态检测
- ✅ DrissionPage浏览器自动化

**缺失部分**:
- ✗ Flask路由定义
- ✗ Blueprint注册
- ✗ 与app_with_upload.py集成

## 推荐实施步骤

### 步骤1: 重构qrcode_login.py

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知乎二维码登录模块
类似CSDN微信扫码登录方案
"""
import time
import os
import base64
import logging
from DrissionPage import ChromiumPage, ChromiumOptions
from flask import Blueprint, request, jsonify
from models import get_db_session, PlatformAccount
from auth import login_required, get_current_user
import json

logger = logging.getLogger(__name__)

zhihu_qrcode_bp = Blueprint('zhihu_qrcode', __name__)

# 全局变量存储登录会话
_zhihu_qr_sessions = {}

class ZhihuQRLogin:
    # ... (保留现有实现) ...

@zhihu_qrcode_bp.route('/api/zhihu/get_qr', methods=['POST'])
@login_required
def get_zhihu_qr():
    """获取知乎二维码"""
    user = get_current_user()
    data = request.json
    account_id = data.get('account_id')

    # ... (实现代码) ...

@zhihu_qrcode_bp.route('/api/zhihu/check_qr_status', methods=['POST'])
@login_required
def check_zhihu_qr_status():
    """检查知乎二维码登录状态"""
    # ... (实现代码) ...

@zhihu_qrcode_bp.route('/api/zhihu/cancel_qr', methods=['POST'])
@login_required
def cancel_zhihu_qr():
    """取消知乎二维码登录"""
    # ... (实现代码) ...
```

### 步骤2: 在app_with_upload.py中注册

```python
# Line 18附近添加:
from qrcode_login import zhihu_qrcode_bp

# Line 54附近添加:
app.register_blueprint(zhihu_qrcode_bp)
```

### 步骤3: 修改前端调用

```javascript
// static/account_config.js

async function testAccountWithQR(accountId) {
    try {
        showLoading('正在获取二维码...');

        // 修改为后端实际端点
        const response = await fetch('/api/zhihu/get_qr', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ account_id: accountId })
        });

        const data = await response.json();

        if (data.success) {
            showQRCodeModal(data.qrcode, data.session_id, accountId);
            pollQRStatus(data.session_id, accountId);
        }
    } catch (error) {
        console.error('QR login error:', error);
        alert('二维码登录失败: ' + error.message);
    }
}

async function pollQRStatus(sessionId, accountId) {
    const pollInterval = setInterval(async () => {
        try {
            // 修改为后端实际端点
            const response = await fetch('/api/zhihu/check_qr_status', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId })
            });

            const data = await response.json();

            if (data.status === 'success') {
                clearInterval(pollInterval);
                closeQRModal();
                alert('登录成功!');
                loadAccounts();
            } else if (data.status === 'scanned') {
                document.getElementById('qr-status').textContent = '✓ 已扫描,请在手机确认';
            } else if (data.status === 'expired') {
                clearInterval(pollInterval);
                alert('二维码已过期,请重新获取');
            }
        } catch (error) {
            clearInterval(pollInterval);
            console.error('Poll error:', error);
        }
    }, 2000);
}
```

### 步骤4: 重启服务

```bash
sudo systemctl restart topn
sudo systemctl status topn
```

### 步骤5: 验证

```bash
# 查看日志
sudo journalctl -u topn -n 50 --no-pager | grep -i 'zhihu\|qr\|二维码'

# 测试端点
curl -X POST http://39.105.12.124:8888/api/zhihu/get_qr \
  -H "Content-Type: application/json" \
  -d '{"account_id": 1}'
```

## 成功标准

修复完成后应该:
1. ✅ 前端点击"测试"按钮,成功弹出二维码
2. ✅ 二维码显示为图片而非HTML错误
3. ✅ 扫码后前端实时显示"已扫描"状态
4. ✅ 登录成功后Cookie自动保存
5. ✅ 数据库中账号状态更新为'success'

## 参考文档

1. **CSDN微信扫码登录实现总结** - `docs/CSDN微信扫码登录实现总结.md`
   - 完整的Blueprint架构
   - 会话管理最佳实践
   - API端点设计参考

2. **CSDN发布器实现完成总结** - `docs/CSDN发布器实现完成总结.md`
   - 模块化设计思路
   - Flask集成方法

3. **代码文件**:
   - `backend/csdn_wechat_login.py` - 成功案例(485行)
   - `backend/qrcode_login.py` - 待集成模块
   - `backend/app_with_upload.py` - 主应用
   - `static/account_config.js` - 前端逻辑

## 总结

**问题**: API端点不匹配导致前端收到HTML 404页面

**原因**: `qrcode_login.py`只有类实现,没有Flask路由集成

**解决**: 参考CSDN微信登录的完整实现,重构为Blueprint并注册到Flask应用

**参考**: CSDN微信扫码登录是完美的实现模板,应该完全参照其架构来重构知乎二维码登录

---

**报告生成时间**: 2025-12-08
**排查工程师**: Claude Code
**优先级**: HIGH - 阻碍用户测试账号登录功能
