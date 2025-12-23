# TOP_N 目录索引

本文档提供TOP_N项目的完整目录索引，方便快速定位文件。

**项目根目录**: `D:\work\code\TOP_N`

## 目录树

```
TOP_N/
├── .claude/                    # Claude Code 配置
├── accounts/                   # 账号配置文件
├── archive/                    # 归档文件
│   ├── chromedriver/          # ChromeDriver旧版本
│   ├── python_installers/     # Python安装包
│   └── temp/                  # 临时文件和旧脚本
├── backend/                    # 后端代码 ⭐
│   ├── __pycache__/           # Python缓存
│   ├── publishers/            # 发布器模块
│   ├── app.py                 # 旧版主应用
│   ├── app_with_upload.py     # 主应用（当前） ⭐
│   ├── zhihu_auto_post_enhanced.py  # 知乎发布（增强版） ⭐
│   ├── login_tester.py        # 登录测试器 ⭐
│   ├── login_tester_enhanced.py
│   ├── login_tester_ultimate.py
│   ├── uploads/               # 文件上传目录
│   └── cookies/               # Cookie存储
├── chromedriver-linux64/      # ChromeDriver
├── data/                      # 数据文件
├── docs/                      # 文档 ⭐
│   ├── 知乎自动登录功能实现说明.md
│   └── ...
├── error/                     # 错误日志
├── frontend/                  # 前端代码
├── scripts/                   # 运维脚本 ⭐
│   ├── check/                 # 检查脚本
│   ├── deploy/                # 部署脚本
│   ├── fix/                   # 修复脚本
│   ├── install/               # 安装脚本
│   ├── test/                  # 测试脚本
│   └── README.md              # 脚本说明
├── static/                    # 静态资源
├── templates/                 # HTML模板
├── uploads/                   # 上传文件
├── README.md                  # 项目说明 ⭐
├── QUICK_DEPLOY.md           # 快速部署指南 ⭐
├── PROJECT_CONFIG.md         # 工程配置 ⭐
├── DIRECTORY_INDEX.md        # 本文件
└── requirements.txt          # Python依赖

```

## 核心文件索引

### 应用主文件
| 文件 | 路径 | 说明 |
|------|------|------|
| 主应用 | `backend/app_with_upload.py` | 当前使用的Flask应用 |
| 旧版应用 | `backend/app.py` | 备用 |

### 知乎功能
| 文件 | 路径 | 说明 |
|------|------|------|
| 增强版发布 | `backend/zhihu_auto_post_enhanced.py` | 含自动登录功能 |
| 登录测试器 | `backend/login_tester.py` | 当前版本 |
| 登录测试器增强版 | `backend/login_tester_enhanced.py` | 备用 |
| 登录测试器终极版 | `backend/login_tester_ultimate.py` | 备用 |

### 部署脚本
| 文件 | 路径 | 说明 |
|------|------|------|
| 标准部署 | `scripts/deploy/deploy_final_correct.py` | ⭐ 当前使用 |
| Cookie功能部署 | `scripts/deploy/deploy_cookie_feature.py` | 历史版本 |
| 登录测试器部署 | `scripts/deploy/deploy_login_tester.py` | 历史版本 |

### 检查脚本
| 文件 | 路径 | 说明 |
|------|------|------|
| 部署验证 | `scripts/check/verify_deployment.py` | ⭐ 验证部署结果 |
| Gunicorn检查 | `scripts/check/check_gunicorn_setup.py` | 检查Gunicorn配置 |
| 启动脚本检查 | `scripts/check/check_start_script.py` | 检查启动方式 |
| 服务器日志 | `scripts/check/check_server_logs.py` | 查看日志 |
| TOP_N日志 | `scripts/check/check_topn_logs.py` | 查看应用日志 |

### 测试脚本
| 文件 | 路径 | 说明 |
|------|------|------|
| API测试 | `scripts/test/test_api.py` | 测试API接口 |
| 本地登录测试 | `scripts/test/local_test_login.py` | 本地测试登录 |
| 增强登录测试 | `scripts/test/test_enhanced_login.py` | 测试增强登录 |

### 文档
| 文件 | 路径 | 说明 |
|------|------|------|
| 项目说明 | `README.md` | 项目总体介绍 |
| 快速部署 | `QUICK_DEPLOY.md` | 部署操作指南 |
| 工程配置 | `PROJECT_CONFIG.md` | 目录规范 |
| 脚本说明 | `scripts/README.md` | 脚本详细说明 |
| 功能实现 | `docs/知乎自动登录功能实现说明.md` | 功能详细文档 |
| 目录索引 | `DIRECTORY_INDEX.md` | 本文件 |

## 按功能分类

### 部署相关
```
scripts/deploy/deploy_final_correct.py    # 标准部署脚本
scripts/check/verify_deployment.py         # 部署验证
QUICK_DEPLOY.md                           # 部署指南
```

### 知乎功能
```
backend/zhihu_auto_post_enhanced.py       # 发布模块
backend/login_tester.py                   # 登录模块
docs/知乎自动登录功能实现说明.md          # 功能文档
```

### 服务器管理
```
scripts/check/check_gunicorn_setup.py     # Gunicorn配置
scripts/check/check_start_script.py       # 启动脚本
scripts/check/check_server_logs.py        # 服务器日志
```

### 测试
```
scripts/test/test_api.py                  # API测试
scripts/test/local_test_login.py          # 登录测试
scripts/test/test_enhanced_login.py       # 增强登录测试
```

### 配置和文档
```
README.md                                 # 项目说明
QUICK_DEPLOY.md                          # 快速部署
PROJECT_CONFIG.md                        # 工程配置
scripts/README.md                        # 脚本说明
requirements.txt                         # 依赖列表
```

## 快速查找

### 我想部署代码
1. 确认在项目根目录: `cd D:\work\code\TOP_N`
2. 运行部署脚本: `python scripts/deploy/deploy_final_correct.py`
3. 验证部署: `python scripts/check/verify_deployment.py`

### 我想查看服务器状态
```bash
python scripts/check/verify_deployment.py          # 完整验证
python scripts/check/check_gunicorn_setup.py       # Gunicorn状态
python scripts/check/check_topn_logs.py            # 查看日志
```

### 我想测试功能
```bash
python scripts/test/test_api.py                    # API测试
python scripts/test/local_test_login.py            # 登录测试
```

### 我想了解某个功能
- 知乎自动登录: `docs/知乎自动登录功能实现说明.md`
- 快速部署: `QUICK_DEPLOY.md`
- 脚本说明: `scripts/README.md`
- 工程规范: `PROJECT_CONFIG.md`

## 文件统计

### Python文件数量
```bash
# 查看所有Python文件
find . -name "*.py" ! -path "*/venv/*" ! -path "*/__pycache__/*" | wc -l
```

### 脚本分类统计
```bash
# 部署脚本
ls scripts/deploy/*.py | wc -l

# 检查脚本
ls scripts/check/*.py | wc -l

# 测试脚本
ls scripts/test/*.py | wc -l

# 安装脚本
ls scripts/install/*.py | wc -l

# 修复脚本
ls scripts/fix/*.py | wc -l
```

## 常用路径

### 本地路径
```
项目根目录:    D:\work\code\TOP_N
后端代码:      D:\work\code\TOP_N\backend
部署脚本:      D:\work\code\TOP_N\scripts\deploy
检查脚本:      D:\work\code\TOP_N\scripts\check
文档目录:      D:\work\code\TOP_N\docs
归档目录:      D:\work\code\TOP_N\archive\temp
```

### 服务器路径
```
项目根目录:    /home/u_topn/TOP_N
后端代码:      /home/u_topn/TOP_N/backend
日志目录:      /home/u_topn/TOP_N/logs
Gunicorn配置:  /home/u_topn/TOP_N/gunicorn_config.py
```

## 更新日志

### 2025-12-08
- 创建目录索引文档
- 整理脚本到scripts目录
- 移除backend目录下的运维脚本
- 添加项目配置文档

---

**最后更新**: 2025-12-08
**文档版本**: 1.0
