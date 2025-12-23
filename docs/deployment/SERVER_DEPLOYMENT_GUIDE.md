# 服务器部署指南 - Blueprints 架构

## 问题诊断

当前报错：
```
GET http://39.105.12.124/admin 500 (INTERNAL SERVER ERROR)
{"message":"权限检查失败: Invalid URL '/api/auth/me': No scheme supplied..."}
```

**根本原因**: 服务器可能还在运行旧版本的 `app_with_upload.py`，而不是新的 blueprints 架构。

## 架构说明

### ❌ 旧版本（不要用于服务器）
- **文件**: `app_with_upload.py`
- **问题**: 第29行有错误的 HTTP 请求代码
```python
auth_response = requests.get('/api/auth/me', cookies=request.cookies)  # 缺少 scheme
```

### ✅ 新版本（服务器应该用这个）
- **主文件**: `backend/app.py`
- **工厂**: `backend/app_factory.py`
- **蓝图**: `backend/blueprints/*`

## 服务器部署步骤

### 步骤1: 确认要上传的修复文件

以下文件已修复，需要上传到服务器：

```
backend/auth_decorators.py               # 增强的管理员权限检查
backend/blueprints/auth.py               # 修复session设置
backend/services/ai_service_v2.py        # 修复import顺序
backend/services/analysis_prompt_service.py   # 添加容错导入
backend/services/article_prompt_service.py    # 添加容错导入
```

### 步骤2: 使用 SCP 上传文件

假设服务器用户是 `u_topn`，路径是 `/data/TOP_N`：

```bash
# 上传 auth_decorators.py
scp backend/auth_decorators.py u_topn@39.105.12.124:/data/TOP_N/backend/

# 上传 auth.py
scp backend/blueprints/auth.py u_topn@39.105.12.124:/data/TOP_N/backend/blueprints/

# 上传 service 文件
scp backend/services/ai_service_v2.py u_topn@39.105.12.124:/data/TOP_N/backend/services/
scp backend/services/analysis_prompt_service.py u_topn@39.105.12.124:/data/TOP_N/backend/services/
scp backend/services/article_prompt_service.py u_topn@39.105.12.124:/data/TOP_N/backend/services/
```

### 步骤3: SSH 登录服务器

```bash
ssh u_topn@39.105.12.124
```

### 步骤4: 检查当前运行的应用

```bash
# 查看正在运行的 Python 进程
ps aux | grep python | grep -E "app\.py|app_with_upload\.py"

# 如果看到 app_with_upload.py 在运行，说明需要切换到 app.py
```

### 步骤5: 检查启动配置

#### 如果使用 systemd

```bash
# 查看服务文件
sudo cat /etc/systemd/system/topn.service

# 或
sudo cat /etc/systemd/system/top_n.service
```

检查 `ExecStart` 行，应该是：
```ini
ExecStart=/path/to/venv/bin/python app.py    # ✅ 正确
```

如果是这样就**错了**：
```ini
ExecStart=/path/to/venv/bin/python app_with_upload.py  # ❌ 错误
```

修改配置：
```bash
sudo nano /etc/systemd/system/topn.service
```

将 `app_with_upload.py` 改为 `app.py`，然后：
```bash
sudo systemctl daemon-reload
sudo systemctl restart topn
```

#### 如果使用 Gunicorn

检查启动命令或配置文件，应该是：
```bash
gunicorn -w 4 -b 0.0.0.0:8080 app:app    # ✅ 正确
```

如果是 `app_with_upload:app` 就需要改成 `app:app`

#### 如果使用 Supervisor

```bash
sudo cat /etc/supervisor/conf.d/topn.conf
```

检查 command 行，确保使用 `app.py`

### 步骤6: 重启应用

根据你的部署方式选择：

```bash
# systemd
sudo systemctl restart topn

# supervisor
sudo supervisorctl restart topn

# 或手动重启 gunicorn
pkill gunicorn
cd /data/TOP_N/backend
gunicorn -w 4 -b 0.0.0.0:8080 app:app
```

### 步骤7: 验证修复

```bash
# 测试登录
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"TopN@2024"}' \
  -c /tmp/cookies.txt

# 测试获取用户信息
curl http://localhost:8080/api/auth/me -b /tmp/cookies.txt

# 测试管理控制台
curl http://localhost:8080/admin -b /tmp/cookies.txt
```

期望结果：
- ✅ 登录返回 200，包含 `"success": true`
- ✅ /api/auth/me 返回 200，包含 admin 用户信息
- ✅ /admin 返回 200，包含 HTML 页面
- ✅ 不再出现 "Invalid URL" 错误

### 步骤8: 浏览器测试

1. 清除浏览器 cookies
2. 访问 `http://39.105.12.124/login`
3. 使用 admin 账户登录
4. 访问 `http://39.105.12.124/admin`
5. 应该能正常打开管理控制台

## 快速诊断命令

在服务器上运行：

```bash
#!/bin/bash
echo "=== 检查运行的应用 ==="
ps aux | grep -E "app\.py|app_with_upload\.py" | grep -v grep

echo -e "\n=== 检查端口 ==="
netstat -tlnp | grep :8080

echo -e "\n=== 测试登录 ==="
curl -s -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"TopN@2024"}' | head -c 200

echo -e "\n=== 检查日志 ==="
tail -20 /data/TOP_N/logs/all.log 2>/dev/null || echo "日志文件不存在"
```

## 检查清单

- [ ] 已上传修复后的 5 个文件
- [ ] 确认服务器启动配置使用 `app.py` 而非 `app_with_upload.py`
- [ ] 已重启应用服务
- [ ] 测试 API 登录成功
- [ ] 测试 /api/auth/me 返回正确
- [ ] 测试 /admin 页面可访问
- [ ] 浏览器清除 cookies 后重新登录测试

## 常见问题

**Q: 文件上传后还是报错**
A: 需要重启应用，Python 不会自动重载代码

**Q: 不知道服务器应用怎么启动的**
A: 运行 `ps aux | grep python` 查看进程，或检查 `/etc/systemd/system/` 和 `/etc/supervisor/conf.d/`

**Q: 数据库中 admin 的 role 不是 'admin'**
A: 运行 SQL：
```sql
UPDATE users SET role='admin' WHERE username='admin';
```

---
创建日期: 2025-12-15
