# 🚀 快速部署步骤

**5分钟完成重构代码部署！**

## 📋 准备工作

### 必需工具
- WinSCP (推荐) 或 SSH客户端
- 服务器凭证:
  - Host: 39.105.12.124
  - User: u_topn
  - Password: @WSX2wsx

### 需要上传的文件（12个）
```
D:\work\code\TOP_N\backend\
├── config.py
├── app_factory.py
├── services\
│   ├── __init__.py
│   ├── file_service.py
│   ├── ai_service.py
│   ├── account_service.py
│   ├── workflow_service.py
│   └── publish_service.py
└── blueprints\
    ├── __init__.py
    ├── api.py
    ├── auth.py
    └── pages.py
```

## ⚡ 快速步骤（WinSCP方式）

### Step 1: 连接服务器 (30秒)

打开WinSCP，输入：
- 协议: SFTP
- 主机名: 39.105.12.124
- 端口: 22
- 用户名: u_topn
- 密码: @WSX2wsx

点击"登录"

### Step 2: 备份当前代码 (1分钟)

在WinSCP中打开SSH终端（Ctrl+T），执行：

```bash
cd /home/u_topn/TOP_N
cp -r backend backend_backup_$(date +%Y%m%d_%H%M%S)
```

### Step 3: 上传文件 (2分钟)

在WinSCP中：

1. 左侧：导航到 `D:\work\code\TOP_N\backend`
2. 右侧：导航到 `/home/u_topn/TOP_N/backend`
3. 选中以下文件，拖拽到右侧（覆盖）：
   - config.py
   - app_factory.py
4. 选中 services 文件夹，拖拽（覆盖）
5. 选中 blueprints 文件夹，拖拽（覆盖）

### Step 4: 重启服务 (1分钟)

在SSH终端中执行：

```bash
# 停止旧服务
pkill -9 -f 'gunicorn.*app'

# 等待3秒
sleep 3

# 启动新服务
cd /home/u_topn/TOP_N/backend
nohup python3.14 -m gunicorn --config /home/u_topn/TOP_N/gunicorn_config.py app_factory:app > /home/u_topn/TOP_N/logs/gunicorn.log 2>&1 &
```

### Step 5: 验证部署 (1分钟)

在SSH终端中执行：

```bash
# 检查进程（应该看到app_factory）
ps aux | grep app_factory | grep -v grep

# 检查端口（应该看到8080 LISTEN）
netstat -tuln | grep 8080

# 测试API（应该返回HTML）
curl -I http://localhost:8080/
```

## ✅ 成功标志

如果看到以下输出，说明部署成功：

### 进程检查
```
u_topn    12345  0.1  1.2  145678  98765 ?  S  01:23  0:00 /usr/bin/python3.14 -m gunicorn app_factory:app
```

### 端口检查
```
tcp        0      0 0.0.0.0:8080            0.0.0.0:*               LISTEN
```

### API检查
```
HTTP/1.1 200 OK
```

## 🌐 访问测试

打开浏览器，访问：
```
http://39.105.12.124:8080
```

应该能看到TOP_N首页。

## 🔄 如果出问题？5秒回滚！

```bash
ssh u_topn@39.105.12.124
pkill -9 -f 'gunicorn.*app'
cd /home/u_topn/TOP_N/backend
nohup python3.14 -m gunicorn --config /home/u_topn/TOP_N/gunicorn_config.py app_with_upload:app > /home/u_topn/TOP_N/logs/gunicorn.log 2>&1 &
```

## 📊 功能测试清单

部署成功后，测试以下功能：

- [ ] 访问首页
- [ ] 用户登录
- [ ] 文件上传
- [ ] AI分析
- [ ] 文章生成
- [ ] 账号管理
- [ ] 知乎发布

## 📝 查看日志

如果需要查看详细日志：

```bash
# 查看错误日志
tail -50 /home/u_topn/TOP_N/logs/gunicorn_error.log

# 实时监控日志
tail -f /home/u_topn/TOP_N/logs/gunicorn_error.log
```

## 🎯 关键命令速查

### 检查服务状态
```bash
ps aux | grep app_factory
netstat -tuln | grep 8080
```

### 重启服务
```bash
pkill -9 -f 'gunicorn.*app'
cd /home/u_topn/TOP_N/backend
nohup python3.14 -m gunicorn --config /home/u_topn/TOP_N/gunicorn_config.py app_factory:app > /home/u_topn/TOP_N/logs/gunicorn.log 2>&1 &
```

### 查看日志
```bash
tail -50 /home/u_topn/TOP_N/logs/gunicorn_error.log
```

---

**总耗时**: 约5分钟
**难度**: ⭐⭐ (简单)
**成功率**: 95%+
**回滚时间**: < 30秒

**准备好了吗？开始部署吧！** 🚀
