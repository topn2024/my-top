# CSDN微信扫码登录实现总结

## 实现时间
2025-12-08

## 实现概述
按照用户要求实现CSDN微信扫码登录功能,类似知乎二维码登录方案,提取微信扫码二维码发送给前端,用户扫码后自动保存Cookie。

## 核心文件

### 1. backend/csdn_wechat_login.py (485行)

**功能特性:**
- 微信扫码二维码提取和展示
- 登录状态轮询检测
- Cookie自动保存
- 会话管理和过期清理
- 数据库集成(PlatformAccount表)

**核心类:**
```python
class CSDNWechatLogin:
    def __init__(self):
        # 初始化浏览器配置
        # 创建cookies目录

    def init_browser(self):
        # 使用DrissionPage初始化浏览器
        # 配置User-Agent和反自动化检测

    def get_wechat_qr_code(self):
        """获取微信扫码登录二维码"""
        # 1. 访问CSDN登录页面
        # 2. 点击微信登录按钮(多选择器尝试)
        # 3. 提取二维码图片:
        #    - 方法1: 从img src属性获取base64
        #    - 方法2: 截图二维码元素
        #    - 方法3: 全页面截图(兜底方案)
        # 4. 返回base64编码的二维码图片

    def check_login_status(self, max_wait=300):
        """轮询检查登录状态"""
        # 每秒检查一次,最多等待5分钟
        # 检测方法:
        #   1. URL是否变化(离开登录页)
        #   2. 页面是否出现用户元素(.user-info, .user-avatar)
        #   3. Cookie中是否有UserToken/uuid_tt_dd
        #   4. 二维码是否过期

    def is_logged_in(self):
        """验证登录状态"""
        # 访问CSDN首页
        # 检查Cookie和页面元素

    def save_cookies(self, username):
        """保存Cookie到JSON文件"""
        # 保存路径: backend/cookies/csdn_{username}.json

    def close(self):
        """关闭浏览器释放资源"""
```

**API端点:**

#### 1. POST /api/csdn/wechat_qr
获取微信扫码登录二维码

**请求:**
```json
{
    "username": "CSDN用户名"
}
```

**响应:**
```json
{
    "success": true,
    "session_id": "1_username_1733600000",
    "qr_image": "data:image/png;base64,iVBORw0KGgoAAAANS...",
    "message": "请使用微信扫描二维码"
}
```

**流程:**
1. 验证用户已登录(@ login_required)
2. 创建CSDNWechatLogin实例
3. 获取微信二维码
4. 生成session_id并保存到_login_sessions
5. 返回base64编码的二维码图片

#### 2. POST /api/csdn/wechat_login_status
检查扫码登录状态(前端轮询)

**请求:**
```json
{
    "session_id": "1_username_1733600000"
}
```

**响应(未登录):**
```json
{
    "success": true,
    "logged_in": false,
    "message": "等待扫码..."
}
```

**响应(已登录):**
```json
{
    "success": true,
    "logged_in": true,
    "message": "登录成功,Cookie已保存"
}
```

**流程:**
1. 验证session_id有效性
2. 调用check_login_status(max_wait=2) 快速检查
3. 如果登录成功:
   - 保存Cookie到文件
   - 更新数据库(PlatformAccount.status = 'success')
   - 清理登录会话
   - 关闭浏览器
4. 返回登录状态

#### 3. POST /api/csdn/cancel_wechat_login
取消扫码登录

**请求:**
```json
{
    "session_id": "1_username_1733600000"
}
```

**响应:**
```json
{
    "success": true,
    "message": "已取消登录"
}
```

**流程:**
1. 关闭对应session的浏览器
2. 删除_login_sessions中的会话
3. 释放资源

### 2. backend/app_with_upload.py (修改)

**添加内容:**
```python
# Line 18: 导入蓝图
from csdn_wechat_login import csdn_wechat_bp

# Line 54: 注册蓝图
app.register_blueprint(csdn_wechat_bp)
```

## 技术架构

### 会话管理
```python
_login_sessions = {
    'session_id': {
        'login': CSDNWechatLogin实例,
        'username': 'CSDN用户名',
        'user_id': 用户ID,
        'created_at': 时间戳
    }
}
```

### 会话清理
```python
def cleanup_expired_sessions():
    """清理超过30分钟的过期会话"""
    # 遍历_login_sessions
    # 删除created_at > 1800秒的会话
    # 关闭对应浏览器
```

## 二维码提取策略

### 多级降级方案:

1. **优先级1**: 从img src属性直接获取
   ```python
   src = qr_img.attr('src')
   if src and src.startswith('data:image'):
       qr_image_base64 = src.split(',')[1]
   ```

2. **优先级2**: 截图二维码元素
   ```python
   qr_img.get_screenshot(qr_path)
   with open(qr_path, 'rb') as f:
       qr_image_base64 = base64.b64encode(f.read()).decode('utf-8')
   ```

3. **优先级3**: 全页面截图(兜底)
   ```python
   self.driver.get_screenshot(screenshot_path)
   ```

### 选择器策略(多选择器尝试):

**微信登录按钮:**
```python
selectors = [
    'text:微信登录',
    'text:微信',
    '.wechat-login',
    '@@title=微信登录',
    'img[alt*="微信"]',
]
```

**二维码图片:**
```python
qr_selectors = [
    'tag:img@@alt=微信扫码',
    '.qrcode img',
    '.login-qr img',
    'tag:img@@src*=qrcode',
    '#qrcode img',
    '.wechat-qr img',
]
```

## 登录状态检测

### 多重检测机制:

1. **URL变化检测**
   ```python
   current_url = self.driver.url
   if current_url != self.login_url and 'login' not in current_url:
       # 可能已登录,进一步验证
   ```

2. **页面元素检测**
   ```python
   success_indicators = [
       '.user-info',
       '.user-avatar',
       '.username',
       'text:退出登录',
   ]
   ```

3. **Cookie检测**
   ```python
   cookies = self.driver.cookies(as_dict=True)
   if 'UserToken' in cookies or 'uuid_tt_dd' in cookies:
       return True
   ```

4. **二维码过期检测**
   ```python
   expired_elem = self.driver.ele('text:二维码已过期', timeout=1)
   if expired_elem:
       return False, '二维码已过期,请重新获取'
   ```

## 前端集成方案(建议)

### 1. 获取二维码
```javascript
// 点击CSDN登录按钮
async function loginCSDN(username) {
    const response = await fetch('/api/csdn/wechat_qr', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username })
    });

    const data = await response.json();
    if (data.success) {
        // 显示二维码
        document.getElementById('qr-image').src = data.qr_image;
        // 开始轮询登录状态
        pollLoginStatus(data.session_id);
    }
}
```

### 2. 轮询登录状态
```javascript
async function pollLoginStatus(sessionId) {
    const interval = setInterval(async () => {
        const response = await fetch('/api/csdn/wechat_login_status', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId })
        });

        const data = await response.json();
        if (data.logged_in) {
            clearInterval(interval);
            alert('登录成功!');
            // 刷新页面或跳转
        } else if (data.message.includes('已过期')) {
            clearInterval(interval);
            alert('二维码已过期,请重新获取');
        }
    }, 2000); // 每2秒检查一次
}
```

### 3. 取消登录
```javascript
async function cancelLogin(sessionId) {
    await fetch('/api/csdn/cancel_wechat_login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
    });
}
```

## 数据库集成

### PlatformAccount表更新:
```python
# 登录成功后
account = db.query(PlatformAccount).filter_by(
    user_id=user.id,
    platform='CSDN',
    username=username
).first()

if account:
    account.status = 'success'
    account.notes = '微信扫码登录成功'
    db.commit()
```

## 部署步骤

### 1. 文件上传
```bash
# csdn_wechat_login.py已上传到服务器
scp csdn_wechat_login.py u_topn@39.105.12.124:/home/u_topn/TOP_N/backend/
```

### 2. app_with_upload.py修改
- Line 18: 添加import
- Line 54: 注册blueprint

### 3. 服务重启
```bash
sudo systemctl restart topn
sudo systemctl status topn
```

## 验证测试

### 1. 检查API端点
```bash
curl -X POST http://39.105.12.124:8888/api/csdn/wechat_qr \
  -H "Content-Type: application/json" \
  -d '{"username":"test_user"}'
```

### 2. 检查日志
```bash
sudo journalctl -u topn -n 50 --no-pager | grep -i csdn
```

### 3. 检查文件
```bash
ls -lh /home/u_topn/TOP_N/backend/csdn_wechat_login.py
ls -lh /home/u_topn/TOP_N/backend/cookies/
```

## 优势对比

### 与知乎二维码登录对比:

| 特性 | 知乎 | CSDN |
|------|------|------|
| 二维码类型 | 知乎APP扫码 | 微信APP扫码 |
| 提取方式 | img src | img src + 截图降级 |
| 轮询检测 | URL变化 | URL+元素+Cookie多重检测 |
| 会话管理 | 全局字典 | 全局字典+过期清理 |
| 数据库集成 | ✓ | ✓ |
| 错误处理 | 基本 | 多级降级 |

## 特殊处理

### 1. 反自动化检测
```python
co.set_argument('--disable-blink-features=AutomationControlled')
co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
```

### 2. 资源管理
- 登录成功后自动关闭浏览器
- 取消登录时主动释放资源
- 定时清理30分钟过期会话

### 3. 容错机制
- 多选择器尝试(微信按钮)
- 多选择器尝试(二维码图片)
- 多重登录检测
- 降级截图方案

## 后续优化建议

### 1. 性能优化
- 浏览器实例池复用
- 二维码缓存机制
- 异步任务队列

### 2. 用户体验
- 二维码刷新功能
- 倒计时显示(5分钟)
- 扫码成功动画

### 3. 安全增强
- Session加密
- 请求限流
- IP白名单

### 4. 监控告警
- 登录成功率统计
- 二维码获取失败告警
- 浏览器崩溃监控

## 文件清单

| 文件 | 状态 | 行数 | 说明 |
|------|------|------|------|
| `backend/csdn_wechat_login.py` | ✅ 已部署 | 485 | 核心模块 |
| `backend/app_with_upload.py` | ✅ 已修改 | +2 | Blueprint注册 |
| `docs/CSDN微信扫码登录实现总结.md` | ✅ 已创建 | - | 本文档 |

## 成功标准验证

✅ 实现微信扫码登录功能
✅ 二维码提取并发送给前端
✅ 登录状态轮询检测
✅ Cookie自动保存
✅ 数据库状态更新
✅ 会话管理和清理
✅ 多重容错机制
✅ API端点集成
✅ 服务部署成功

## 总结

成功实现CSDN微信扫码登录功能,采用与知乎类似的架构设计,通过DrissionPage提取微信二维码,前端轮询检测登录状态,登录成功后自动保存Cookie并更新数据库。

**核心价值:**
- 统一的扫码登录体验
- 完善的容错降级机制
- 自动化Cookie管理
- 与现有系统无缝集成

**下一步:**
建议添加前端页面展示二维码,并实现轮询检测逻辑,完成端到端的用户登录流程。
