# TOP_N 快速部署指南

本文档提供TOP_N项目的快速部署和常用操作指南。

## 目录结构

```
D:\work\code\TOP_N/
├── backend/                 # 后端代码
│   ├── app_with_upload.py  # 主应用 (带文件上传)
│   ├── zhihu_auto_post_enhanced.py  # 知乎自动发布(增强版)
│   ├── login_tester.py     # 知乎登录测试器
│   └── ...
├── scripts/                 # 运维脚本
│   ├── deploy/             # 部署脚本
│   ├── check/              # 检查脚本
│   ├── test/               # 测试脚本
│   ├── install/            # 安装脚本
│   ├── fix/                # 修复脚本
│   └── README.md           # 脚本说明
├── docs/                    # 文档
├── archive/                 # 归档文件
│   └── temp/               # 临时文件
└── README.md               # 项目说明
```

## 服务器信息

### 生产环境
- **地址**: 39.105.12.124:8080
- **用户**: u_topn
- **密码**: TopN@2024
- **路径**: /home/u_topn/TOP_N/backend
- **访问**: http://39.105.12.124:8080

### 服务管理
- **运行方式**: Gunicorn
- **配置文件**: /home/u_topn/TOP_N/gunicorn_config.py
- **工作进程**: 5个 (CPU核心数 * 2 + 1)
- **日志路径**: /home/u_topn/TOP_N/logs/

## 常用操作

### 1. 部署到服务器

```bash
# 切换到项目目录
cd D:\work\code\TOP_N

# 运行部署脚本
python scripts/deploy/deploy_final_correct.py
```

部署脚本会自动完成：
1. 连接服务器
2. 备份现有文件
3. 上传新文件
4. 验证代码集成
5. 停止旧服务
6. 启动新服务
7. 验证服务状态

### 2. 验证部署

```bash
# 验证部署是否成功
python scripts/check/verify_deployment.py
```

检查项目：
- Gunicorn进程状态
- 端口8080监听状态
- 已部署文件完整性
- 代码集成验证
- HTTP服务响应

### 3. 查看服务器日志

```bash
# 查看Gunicorn错误日志
python scripts/check/check_topn_logs.py

# 或直接SSH登录查看
ssh u_topn@39.105.12.124
tail -f /home/u_topn/TOP_N/logs/gunicorn_error.log
```

### 4. 手动重启服务

如需手动重启服务：

```bash
# SSH登录服务器
ssh u_topn@39.105.12.124

# 停止所有Gunicorn进程
pkill -9 -f 'gunicorn.*app_with_upload'

# 启动服务
cd /home/u_topn/TOP_N/backend
nohup /usr/local/bin/python3.14 /home/u_topn/.local/bin/gunicorn \
  --config /home/u_topn/TOP_N/gunicorn_config.py \
  app_with_upload:app > /home/u_topn/TOP_N/logs/gunicorn.log 2>&1 &

# 验证服务
ps aux | grep gunicorn
netstat -tuln | grep 8080
```

## 知乎自动登录功能

### 功能说明
已实现三级登录策略：
1. **Cookie优先** - 首先尝试使用保存的Cookie登录
2. **密码fallback** - Cookie失效时自动使用账号密码登录
3. **自动保存** - 登录成功后自动保存Cookie

### 工作流程
```
发布文章
  ↓
检查Cookie
  ↓
Cookie存在? → 是 → 使用Cookie登录
  ↓ 否
自动密码登录
  ↓
保存Cookie
  ↓
发布文章
```

### 配置测试账号
1. 访问 http://39.105.12.124:8080
2. 进入"账号管理"
3. 添加知乎测试账号（用户名+密码）
4. 系统会自动使用该账号进行登录

### 相关文件
- `backend/zhihu_auto_post_enhanced.py` - 增强版发布模块（含自动登录）
- `backend/login_tester.py` - 登录测试器模块
- `backend/app_with_upload.py` - 主应用（已集成）

## 目录规范

### 脚本存放规则
所有TOP_N相关脚本必须放在 `D:\work\code\TOP_N` 目录下：

- **部署脚本** → `scripts/deploy/`
- **检查脚本** → `scripts/check/`
- **测试脚本** → `scripts/test/`
- **安装脚本** → `scripts/install/`
- **修复脚本** → `scripts/fix/`
- **临时文件** → `archive/temp/`

### 不要使用的目录
- ❌ `C:\Users\lenovo\` - 用户主目录
- ❌ `D:\work\code\TOP_N\backend\` - 后端代码目录（除业务代码外）
- ✅ `D:\work\code\TOP_N\scripts\` - 正确的脚本目录

## 常见问题

### Q1: 部署后端口被占用
**A**: 运行部署脚本会自动处理端口占用问题。如果手动操作：
```bash
ssh u_topn@39.105.12.124
pkill -9 -f 'gunicorn.*app_with_upload'
fuser -k 8080/tcp
```

### Q2: 服务启动失败
**A**: 查看错误日志：
```bash
tail -50 /home/u_topn/TOP_N/logs/gunicorn_error.log
```

### Q3: 代码更新后如何部署
**A**: 直接运行部署脚本即可：
```bash
cd D:\work\code\TOP_N
python scripts/deploy/deploy_final_correct.py
```

### Q4: 如何测试知乎登录功能
**A**:
1. 在Web界面配置知乎账号
2. 尝试发布一篇测试文章
3. 查看日志确认登录流程
```bash
tail -f /home/u_topn/TOP_N/logs/gunicorn_error.log
```

## 最佳实践

1. **部署前**
   - 确认代码在本地通过测试
   - 确认工作目录为 `D:\work\code\TOP_N`
   - 使用标准部署脚本 `scripts/deploy/deploy_final_correct.py`

2. **部署后**
   - 运行验证脚本 `scripts/check/verify_deployment.py`
   - 检查服务状态和日志
   - 在Web界面测试核心功能

3. **遇到问题**
   - 查看错误日志
   - 使用对应的check脚本诊断
   - 使用对应的fix脚本修复

4. **脚本管理**
   - 新脚本按功能分类存放
   - 旧版本脚本移至archive/temp/
   - 避免在backend目录创建运维脚本

## 相关文档

- **项目说明**: README.md
- **脚本说明**: scripts/README.md
- **实现文档**: docs/知乎自动登录功能实现说明.md
- **部署确认**: backend/部署完成确认单.md

## 联系方式

有问题请查阅文档或检查日志文件。

---

**最后更新**: 2025-12-08
**当前版本**: 知乎自动登录功能已部署
