# TOP_N 工程配置

本文档记录TOP_N项目的工程配置和目录规范。

## 工程根目录

```
D:\work\code\TOP_N
```

**重要**: 所有TOP_N相关的代码、脚本、文档都必须放在此目录下。

## 目录结构

```
TOP_N/
├── backend/                    # 后端业务代码目录
│   ├── app.py                 # 旧版主应用
│   ├── app_with_upload.py     # 主应用（当前使用）
│   ├── zhihu_auto_post_enhanced.py  # 知乎自动发布（增强版）
│   ├── login_tester.py        # 登录测试器（当前版本）
│   ├── login_tester_enhanced.py     # 登录测试器（增强版）
│   ├── login_tester_ultimate.py     # 登录测试器（终极版）
│   ├── uploads/               # 上传文件目录
│   ├── cookies/               # Cookie存储目录
│   └── ...                    # 其他业务代码
│
├── frontend/                   # 前端代码（如果有）
│
├── scripts/                    # 运维脚本目录
│   ├── deploy/                # 部署脚本
│   │   ├── deploy_final_correct.py  # 标准部署脚本 ⭐
│   │   └── ...
│   ├── check/                 # 检查和验证脚本
│   │   ├── verify_deployment.py     # 部署验证脚本 ⭐
│   │   ├── check_gunicorn_setup.py  # 检查Gunicorn配置
│   │   ├── check_start_script.py    # 检查启动脚本
│   │   └── ...
│   ├── test/                  # 测试脚本
│   │   ├── test_api.py
│   │   ├── test_markdown_removal.py
│   │   └── ...
│   ├── install/               # 安装和配置脚本
│   │   └── ...
│   ├── fix/                   # 修复脚本
│   │   └── ...
│   └── README.md              # 脚本说明文档
│
├── docs/                       # 文档目录
│   ├── 知乎自动登录功能实现说明.md
│   └── ...
│
├── archive/                    # 归档目录
│   └── temp/                  # 临时文件/旧版本脚本
│       ├── auto_deploy_zhihu_login.py
│       ├── check_port_3001.py
│       ├── deploy_now.py
│       └── ...
│
├── logs/                       # 本地日志（如果有）
│
├── README.md                   # 项目说明
├── QUICK_DEPLOY.md            # 快速部署指南
├── PROJECT_CONFIG.md          # 本文件
└── requirements.txt           # Python依赖

```

## 目录用途说明

### backend/ - 后端业务代码
**只存放业务逻辑代码，不存放运维脚本**

允许的文件类型：
- ✅ 应用主文件 (app.py, app_with_upload.py)
- ✅ 业务模块 (zhihu_auto_post_*.py, login_tester*.py)
- ✅ 工具类 (utils.py, helpers.py)
- ✅ 配置文件 (config.py, settings.py)
- ✅ 数据文件目录 (uploads/, cookies/, data/)

不允许的文件类型：
- ❌ 部署脚本 (deploy_*.py)
- ❌ 检查脚本 (check_*.py, verify_*.py)
- ❌ 测试脚本 (test_*.py)
- ❌ 修复脚本 (fix_*.py)

### scripts/ - 运维脚本
**所有运维相关脚本的统一存放位置**

子目录分类：
- `deploy/` - 部署相关脚本
- `check/` - 检查、验证、监控脚本
- `test/` - 测试脚本
- `install/` - 安装和环境配置脚本
- `fix/` - 问题修复脚本

### docs/ - 文档
**项目文档、说明、指南**

文档类型：
- 功能说明文档
- 实现详细文档
- API文档
- 部署文档

### archive/ - 归档
**旧版本文件、临时文件、废弃代码**

- `temp/` - 临时脚本和旧版本脚本
- 原则：不再使用的文件移至此处，不要删除

## 脚本命名规范

### 部署脚本
- 格式: `deploy_<功能描述>.py`
- 示例:
  - `deploy_final_correct.py` - 标准部署脚本
  - `deploy_zhihu_login.py` - 知乎登录功能部署
  - `deploy_cookie_feature.py` - Cookie功能部署

### 检查脚本
- 格式: `check_<检查对象>.py` 或 `verify_<验证内容>.py`
- 示例:
  - `check_gunicorn_setup.py` - 检查Gunicorn配置
  - `verify_deployment.py` - 验证部署结果
  - `check_server_logs.py` - 查看服务器日志

### 测试脚本
- 格式: `test_<测试对象>.py`
- 示例:
  - `test_api.py` - API测试
  - `test_zhihu_login.py` - 知乎登录测试

### 安装脚本
- 格式: `install_<安装内容>.py`
- 示例:
  - `install_python314.py` - 安装Python 3.14
  - `install_selenium.py` - 安装Selenium

### 修复脚本
- 格式: `fix_<问题描述>.py`
- 示例:
  - `fix_deployment.py` - 修复部署问题
  - `fix_api_routes.py` - 修复API路由

## 工作流程规范

### 1. 开发新功能
```bash
# 1. 在backend/目录编写业务代码
# 2. 在scripts/test/目录创建测试脚本
# 3. 本地测试通过
# 4. 在scripts/deploy/目录创建或更新部署脚本
```

### 2. 部署到服务器
```bash
# 始终从项目根目录操作
cd D:\work\code\TOP_N

# 使用标准部署脚本
python scripts/deploy/deploy_final_correct.py

# 验证部署
python scripts/check/verify_deployment.py
```

### 3. 脚本管理
```bash
# 创建新脚本 - 存放到对应目录
scripts/deploy/new_deploy_script.py
scripts/check/new_check_script.py

# 旧脚本归档 - 移动到archive/temp
mv scripts/deploy/old_script.py archive/temp/

# 不要删除 - 保留历史记录
```

## 禁止使用的目录

以下目录不得用于存放TOP_N项目相关文件：

- ❌ `C:\Users\lenovo\` - Windows用户主目录
- ❌ `C:\Users\lenovo\Documents\`
- ❌ `C:\Users\lenovo\Desktop\`
- ❌ `D:\` 根目录
- ❌ 任何非 `D:\work\code\TOP_N` 的目录

**例外**: 操作系统级别的配置文件（如SSH配置）

## 服务器目录结构

服务器端的目录结构：

```
/home/u_topn/TOP_N/
├── backend/                    # 后端代码
│   ├── app_with_upload.py
│   ├── zhihu_auto_post_enhanced.py
│   ├── login_tester.py
│   ├── uploads/
│   └── cookies/
├── logs/                       # 日志文件
│   ├── gunicorn_access.log
│   ├── gunicorn_error.log
│   └── app.log
├── venv/                       # Python虚拟环境
├── gunicorn_config.py         # Gunicorn配置
├── start.sh                   # 启动脚本
└── requirements.txt           # 依赖列表
```

## 当前活跃脚本

### 部署
- `scripts/deploy/deploy_final_correct.py` - **标准部署脚本**

### 检查
- `scripts/check/verify_deployment.py` - **部署验证**
- `scripts/check/check_gunicorn_setup.py` - Gunicorn配置检查
- `scripts/check/check_start_script.py` - 启动脚本检查

### 测试
- `scripts/test/test_api.py` - API测试

## 环境变量

项目相关的环境变量（如需要）：

```bash
# 本地开发
TOP_N_ROOT=D:\work\code\TOP_N
TOP_N_ENV=development

# 服务器
TOP_N_ROOT=/home/u_topn/TOP_N
TOP_N_ENV=production
```

## Git 配置

`.gitignore` 应包含：

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/

# 项目特定
/backend/uploads/*
/backend/cookies/*
/logs/*
*.log

# 临时文件
/archive/temp/*

# IDE
.vscode/
.idea/
*.swp
*.swo
```

## 检查清单

在提交代码前检查：

- [ ] 所有业务代码在 `backend/` 目录
- [ ] 所有运维脚本在 `scripts/` 对应子目录
- [ ] 临时文件移至 `archive/temp/`
- [ ] 文档更新在 `docs/` 目录
- [ ] 没有文件在项目根目录外
- [ ] 脚本使用相对路径或配置路径
- [ ] README 和文档已更新

## 常见错误

### ❌ 错误做法
```bash
# 在backend目录创建运维脚本
D:\work\code\TOP_N\backend\deploy_something.py

# 使用用户目录
C:\Users\lenovo\my_script.py

# 使用绝对路径硬编码
D:\work\code\TOP_N\backend\...
```

### ✅ 正确做法
```bash
# 运维脚本放在scripts对应目录
D:\work\code\TOP_N\scripts\deploy\deploy_something.py

# 所有文件在项目目录
D:\work\code\TOP_N\...

# 使用相对路径
os.path.join(os.path.dirname(__file__), '..', 'backend')
```

## 文档更新

当有重要变更时，需要更新以下文档：

1. `README.md` - 项目总体说明
2. `QUICK_DEPLOY.md` - 快速部署指南
3. `scripts/README.md` - 脚本说明
4. `PROJECT_CONFIG.md` - 本文件（工程配置）
5. 相关功能文档在 `docs/` 目录

---

**配置版本**: 1.0
**最后更新**: 2025-12-08
**更新人**: Claude Code
