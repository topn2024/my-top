# 重构代码手动部署指南

由于权限限制，推荐使用WinSCP或手动SSH方式部署。

## 方式一：使用WinSCP（推荐）

### 1. 连接服务器

- Host: 39.105.12.124
- Port: 22
- Username: u_topn
- Password: @WSX2wsx

### 2. 备份当前代码

在服务器上执行：
```bash
cd /home/u_topn/TOP_N
cp -r backend backend_backup_$(date +%Y%m%d_%H%M%S)
```

### 3. 上传文件

从本地 `D:\work\code\TOP_N` 上传以下文件到 `/home/u_topn/TOP_N`:

**核心文件:**
- `backend/config.py`
- `backend/app_factory.py`

**服务层 (backend/services/):**
- `__init__.py`
- `file_service.py`
- `ai_service.py`
- `account_service.py`
- `workflow_service.py`
- `publish_service.py`

**蓝图层 (backend/blueprints/):**
- `__init__.py`
- `api.py`
- `auth.py`
- `pages.py`

### 4. 重启服务

SSH登录服务器：
```bash
ssh u_topn@39.105.12.124
```

停止旧服务：
```bash
pkill -9 -f 'gunicorn.*app'
```

启动新服务（使用app_factory）：
```bash
cd /home/u_topn/TOP_N/backend
nohup python3.14 -m gunicorn --config /home/u_topn/TOP_N/gunicorn_config.py app_factory:app > /home/u_topn/TOP_N/logs/gunicorn.log 2>&1 &
```

### 5. 验证服务

检查进程：
```bash
ps aux | grep app_factory | grep -v grep
```

检查端口：
```bash
netstat -tuln | grep 8080
```

测试API：
```bash
curl http://localhost:8080/
```

查看日志：
```bash
tail -f /home/u_topn/TOP_N/logs/gunicorn_error.log
```

## 方式二：使用SCP命令

### 1. 从Windows本地上传文件

打开Git Bash或PowerShell，执行：

```bash
# 上传config.py
scp /d/work/code/TOP_N/backend/config.py u_topn@39.105.12.124:/home/u_topn/TOP_N/backend/

# 上传app_factory.py
scp /d/work/code/TOP_N/backend/app_factory.py u_topn@39.105.12.124:/home/u_topn/TOP_N/backend/

# 上传services目录
scp -r /d/work/code/TOP_N/backend/services u_topn@39.105.12.124:/home/u_topn/TOP_N/backend/

# 上传blueprints目录
scp -r /d/work/code/TOP_N/backend/blueprints u_topn@39.105.12.124:/home/u_topn/TOP_N/backend/
```

### 2. SSH登录并重启服务

```bash
ssh u_topn@39.105.12.124
pkill -9 -f 'gunicorn.*app'
cd /home/u_topn/TOP_N/backend
nohup python3.14 -m gunicorn --config /home/u_topn/TOP_N/gunicorn_config.py app_factory:app > /home/u_topn/TOP_N/logs/gunicorn.log 2>&1 &
```

## 回滚方案

如果新版本有问题，回滚到旧版本：

```bash
ssh u_topn@39.105.12.124
pkill -9 -f 'gunicorn.*app'
cd /home/u_topn/TOP_N/backend
nohup python3.14 -m gunicorn --config /home/u_topn/TOP_N/gunicorn_config.py app_with_upload:app > /home/u_topn/TOP_N/logs/gunicorn.log 2>&1 &
```

## 测试清单

部署后需要测试以下功能：

- [ ] 访问首页: http://39.105.12.124:8080
- [ ] 用户登录
- [ ] 文件上传
- [ ] AI分析
- [ ] 文章生成
- [ ] 账号管理
- [ ] 知乎发布

## 常见问题

### Q: 如何确认使用了新架构？

A: 检查进程命令行中是否包含`app_factory`:
```bash
ps aux | grep gunicorn | grep app_factory
```

### Q: 如何查看错误日志？

A:
```bash
tail -100 /home/u_topn/TOP_N/logs/gunicorn_error.log
```

### Q: 服务无法启动？

A: 检查Python路径和配置文件：
```bash
which python3.14
cat /home/u_topn/TOP_N/gunicorn_config.py
```

## 新架构优势

- ✅ 模块化设计，代码清晰
- ✅ 服务层解耦，易于维护
- ✅ 蓝图组织，路由清晰
- ✅ 配置集中管理
- ✅ 易于测试和扩展

---
**文档版本**: 1.0
**更新时间**: 2025-12-09
