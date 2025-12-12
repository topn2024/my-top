# 知乎二维码自动登录和发布流程

## 概述

实现了完整的二维码登录和自动发布流程，用户点击"开始发布"后如果未配置账号，会自动弹出二维码进行登录，登录成功后自动保存Cookie并发布文章。

## 完整流程

### 1. 用户点击"开始发布"按钮

前端调用 `/api/publish_zhihu` 接口

### 2. 系统检测是否有账号配置

```javascript
// static/publish.js
async function publishToZhihu(article) {
    const response = await fetch('/api/publish_zhihu', {
        method: 'POST',
        body: JSON.stringify({
            title: article.title,
            content: article.content,
            article_id: article.id || 0
        })
    });

    const data = await response.json();

    // 检查是否需要二维码登录
    if (data.requireQRLogin) {
        await handleQRLogin(article);
        return;
    }
}
```

### 3. 后端返回需要QR登录

```python
# backend/services/publish_service.py
def publish_to_zhihu(self, user_id: int, account_id: int, article_id: int, title: str, content: str):
    if account_id == 0:
        # 没有配置账号，要求二维码登录
        return {
            'success': False,
            'requireQRLogin': True,
            'message': '请先使用二维码登录知乎账号'
        }
```

### 4. 前端获取二维码

```javascript
// static/publish.js
async function handleQRLogin(article) {
    // 1. 获取二维码
    const response = await fetch('/api/zhihu/qr_login/start', {
        method: 'POST'
    });

    const data = await response.json();

    // 2. 显示二维码弹窗
    showQRCodeModal(data.qr_code, data.session_id, article);
}
```

### 5. 后端生成二维码

```python
# backend/blueprints/api.py
@api_bp.route('/zhihu/qr_login/start', methods=['POST'])
@login_required
def start_zhihu_qr_login():
    qr_login = ZhihuQRLogin()
    success, qr_base64, message = qr_login.get_qr_code()

    if success:
        # 保存会话
        session_id = f"zhihu_login_{user.id}"
        api_bp.qr_login_sessions[session_id] = qr_login

        return jsonify({
            'success': True,
            'qr_code': f'data:image/png;base64,{qr_base64}',
            'session_id': session_id
        })
```

### 6. 获取二维码的实现（混合方案）

```python
# backend/zhihu_auth/zhihu_qr_login.py
class ZhihuQRLogin:
    def get_qr_code(self):
        # 方案1：尝试使用DrissionPage获取真实二维码（带超时25秒）
        result_container = {}
        thread = threading.Thread(target=self._get_qr_with_timeout, args=(result_container, 20))
        thread.start()
        thread.join(timeout=25)

        if result_container.get('success'):
            return True, result_container['qr_base64'], result_container['message']

        # 方案2：降级方案 - 生成提示图片
        return self._get_fallback_qr_code()
```

### 7. 前端显示二维码并等待登录

```javascript
// static/publish.js
function showQRCodeModal(qrCodeDataUrl, sessionId, article) {
    // 显示二维码弹窗
    modal.innerHTML = `
        <img src="${qrCodeDataUrl}" alt="登录二维码">
        <p id="qr-login-status">等待扫码中...</p>
    `;

    // 开始等待登录（阻塞式）
    startQRLoginPolling(sessionId, article, modal);
}

async function startQRLoginPolling(sessionId, article, modal) {
    // 调用wait端点（会阻塞直到登录成功或超时120秒）
    const response = await fetch('/api/zhihu/qr_login/wait', {
        method: 'POST',
        body: JSON.stringify({
            session_id: sessionId,
            timeout: 120
        })
    });

    const data = await response.json();

    if (data.success && data.logged_in) {
        // 登录成功，关闭弹窗
        document.body.removeChild(modal);
        // 重新发布文章
        await publishToZhihu(article);
    }
}
```

### 8. 后端等待登录完成

```python
# backend/blueprints/api.py
@api_bp.route('/zhihu/qr_login/wait', methods=['POST'])
@login_required
def wait_zhihu_qr_login():
    qr_login = api_bp.qr_login_sessions[session_id]

    # 等待登录（阻塞式，最多120秒）
    success, message = qr_login.wait_for_login(timeout=timeout)

    if success:
        # 登录成功，保存Cookie
        qr_login.save_cookies(user.username)

        # 清理会话
        qr_login.close()
        del api_bp.qr_login_sessions[session_id]

        return jsonify({
            'success': True,
            'logged_in': True,
            'message': '登录成功，Cookie已保存'
        })
```

### 9. 等待登录的实现

```python
# backend/zhihu_auth/zhihu_qr_login.py
class ZhihuQRLogin:
    def wait_for_login(self, timeout=120):
        start_time = time.time()

        while time.time() - start_time < timeout:
            current_url = self.driver.url

            # 检查是否已经跳转（登录成功）
            if 'zhihu.com' in current_url and '/signin' not in current_url:
                logger.info('✓ 检测到URL跳转，登录成功!')
                time.sleep(2)  # 等待页面稳定
                return True, '登录成功'

            # 检查页面内容
            page_html = self.driver.html
            if any(x in page_html for x in ['我的主页', '退出登录', '个人中心']):
                logger.info('✓ 检测到登录标识，登录成功!')
                return True, '登录成功'

            time.sleep(2)  # 每2秒检查一次

        return False, '登录超时'
```

### 10. 保存Cookie

```python
# backend/zhihu_auth/zhihu_qr_login.py
class ZhihuQRLogin:
    def save_cookies(self, username):
        cookies = self.driver.cookies()
        cookie_file = os.path.join(self.cookies_dir, f'zhihu_{username}.json')

        # 转换为列表格式
        cookie_list = []
        for cookie in cookies:
            cookie_list.append({
                'name': cookie.get('name'),
                'value': cookie.get('value'),
                'domain': cookie.get('domain'),
                'path': cookie.get('path')
            })

        with open(cookie_file, 'w', encoding='utf-8') as f:
            json.dump(cookie_list, f, ensure_ascii=False, indent=2)

        logger.info(f'✓ Cookie已保存: {cookie_file}')
```

### 11. 自动发布文章

登录成功后，前端自动调用 `publishToZhihu(article)` 重新发布，这次有Cookie了就能成功发布。

## 技术要点

### 1. 超时控制

- **DrissionPage获取二维码**：25秒超时，超时后使用降级方案
- **等待用户登录**：120秒超时
- **Gunicorn worker**：120秒超时（需要确保wait操作在此之前完成）

### 2. 降级方案

当DrissionPage获取二维码失败或超时时，生成一个提示图片告诉用户去账号配置页面添加账号。

### 3. 阻塞式等待 vs 轮询

- **旧方案（轮询）**：前端每2秒调用一次check接口，效率低
- **新方案（阻塞）**：调用wait接口，服务器端阻塞等待，登录成功或超时后返回，减少请求次数

### 4. 会话管理

使用 `api_bp.qr_login_sessions` 字典存储QR登录会话，`session_id` 格式为 `zhihu_login_{user_id}`

## API端点

### 1. `/api/publish_zhihu` (POST)

发布文章到知乎

**请求：**
```json
{
    "title": "文章标题",
    "content": "文章内容",
    "article_id": 123
}
```

**响应（需要QR登录）：**
```json
{
    "success": false,
    "requireQRLogin": true,
    "message": "请先使用二维码登录知乎账号"
}
```

### 2. `/api/zhihu/qr_login/start` (POST)

开始二维码登录，获取二维码

**响应：**
```json
{
    "success": true,
    "qr_code": "data:image/png;base64,iVBORw0KGgo...",
    "session_id": "zhihu_login_1",
    "message": "请使用知乎APP扫码登录"
}
```

### 3. `/api/zhihu/qr_login/wait` (POST)

等待二维码登录完成（阻塞式）

**请求：**
```json
{
    "session_id": "zhihu_login_1",
    "timeout": 120
}
```

**响应（成功）：**
```json
{
    "success": true,
    "logged_in": true,
    "message": "登录成功，Cookie已保存"
}
```

**响应（失败）：**
```json
{
    "success": false,
    "logged_in": false,
    "message": "登录超时，请重试"
}
```

## 部署步骤

1. 部署二维码登录模块：
```bash
python scripts/deploy_complete_qr_publish.py
```

2. 更新前端使用wait端点：
```bash
python scripts/update_frontend_wait.py
```

3. 重启服务：
```bash
ssh u_topn@39.105.12.124 "pkill -f gunicorn; bash /home/u_topn/TOP_N/start_service.sh"
```

## 测试流程

1. 访问 http://39.105.12.124:8080
2. 登录用户账号
3. 分析公司，生成文章
4. 点击"开始发布"按钮
5. 弹出二维码
6. 使用知乎APP扫码登录
7. 登录成功后自动发布文章

## 文件清单

### 后端文件

- `backend/zhihu_auth/zhihu_qr_login.py` - 二维码登录模块
- `backend/blueprints/api.py` - API路由（包含3个QR相关端点）
- `backend/services/publish_service.py` - 发布服务（返回requireQRLogin标志）

### 前端文件

- `static/publish.js` - 发布页面JavaScript（包含完整QR登录流程）

### 部署脚本

- `scripts/deploy_complete_qr_publish.py` - 部署完整QR登录流程
- `scripts/update_frontend_wait.py` - 更新前端使用wait端点
- `scripts/fix/use_requests_qr.py` - 使用requests的降级方案（已弃用）

## 注意事项

1. **超时配置**：确保Gunicorn的timeout > wait端点的timeout
2. **会话清理**：登录成功或失败后要清理qr_login_sessions
3. **错误处理**：每个环节都要有适当的错误处理和用户提示
4. **浏览器资源**：确保wait_for_login结束后关闭浏览器
5. **Cookie安全**：Cookie文件保存在 `backend/cookies/` 目录，注意权限设置

## 未来优化

1. 使用Redis存储QR登录会话，支持多worker
2. 添加二维码刷新功能（二维码过期后）
3. 支持多平台二维码登录（微信公众号、头条等）
4. 添加登录状态实时推送（WebSocket）
5. 优化DrissionPage访问知乎的成功率
