# TOP_N - 大模型推广平台

让您的公司在各大主流大模型推荐中排名靠前

[![Version](https://img.shields.io/badge/version-2.0-blue.svg)](https://github.com/topn2024/TOP_N)
[![Python](https://img.shields.io/badge/python-3.6%2B-brightgreen.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/flask-2.0%2B-orange.svg)](https://flask.palletsprojects.com)

## 📋 项目简介

TOP_N是一个智能推广平台，帮助企业提升在大模型推荐中的排名和曝光度。

### 核心功能

1. **智能分析** - 使用千问AI深度分析公司/产品信息
2. **自动生成** - 一键生成多篇专业推广文章
3. **平台推荐** - 推荐最佳发布平台
4. **自动发布** - 支持知乎等平台自动发布
5. **效果跟踪** - 记录发布历史和效果

## ✨ 功能特点

- 🤖 **AI驱动**: 基于阿里云千问大模型
- 📝 **批量生成**: 一次生成多篇不同角度的文章
- 🌐 **多平台**: 支持知乎、CSDN、掘金等平台
- 🔐 **安全认证**: 用户认证和权限管理
- 📊 **数据管理**: 工作流和发布历史管理
- 🚀 **自动登录**: Cookie优先，密码fallback

## 🏗️ 技术架构

### 技术栈

- **后端**: Python 3.6+ + Flask 2.0
- **前端**: HTML5 + CSS3 + JavaScript
- **AI**: 阿里云千问API
- **数据库**: SQLite (可扩展到MySQL)
- **部署**: Gunicorn + Systemd

### 架构设计

```
TOP_N/
├── backend/              # 后端代码
│   ├── config.py        # 配置管理
│   ├── app_factory.py   # 应用工厂
│   ├── services/        # 服务层
│   └── blueprints/      # 路由蓝图
├── frontend/            # 前端代码（可选）
├── templates/           # HTML模板
├── static/              # 静态资源
├── scripts/             # 运维脚本
└── docs/               # 项目文档
```

## 🚀 快速开始

### 环境要求

- Python 3.6+
- pip
- virtualenv (可选)

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/topn2024/TOP_N.git
cd TOP_N
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**
```bash
export QIANWEN_API_KEY=your_api_key
export TOPN_SECRET_KEY=your_secret_key
export FLASK_ENV=development
```

4. **初始化数据库**
```bash
cd backend
python init_db.py
```

5. **运行应用**
```bash
# 开发环境
python app_factory.py

# 生产环境
gunicorn --config gunicorn_config.py app_factory:app
```

6. **访问应用**
```
http://localhost:3001
```

## 📚 文档导航

### 快速参考
- [快速部署指南](QUICK_DEPLOY.md)
- [工程配置说明](PROJECT_CONFIG.md)
- [目录结构索引](DIRECTORY_INDEX.md)

### 开发文档
- [代码重构指南](docs/REFACTORING_GUIDE.md)
- [服务使用示例](docs/SERVICE_USAGE_EXAMPLES.md)
- [迁移指南](docs/MIGRATION_GUIDE.md)
- [API文档](docs/API.md) (计划中)

### 运维文档
- [脚本使用说明](scripts/README.md)
- [部署文档](docs/DEPLOYMENT.md) (计划中)
- [故障排查](docs/TROUBLESHOOTING.md) (计划中)

## 💻 使用指南

### 1. 注册/登录
- 访问系统首页
- 注册新账号或使用已有账号登录

### 2. 输入信息
- 填写公司/产品名称
- 描述业务领域、核心优势
- 可选：上传补充资料（PDF、Word、TXT）

### 3. AI分析
- 系统自动分析企业信息
- 从多个维度进行评估：
  - 行业定位
  - 核心优势
  - 目标用户
  - 技术特点
  - 市场前景

### 4. 生成文章
- 选择需要生成的文章数量（1-5篇）
- 系统自动生成不同角度的推广文章
- 每篇文章800-1500字，适合各大平台

### 5. 配置账号
- 进入"账号管理"
- 添加发布平台账号（知乎、CSDN等）
- 密码加密存储，安全可靠

### 6. 发布推广
- 选择文章和目标平台
- 一键自动发布
- 查看发布历史和状态

## 🔧 部署信息

### 生产环境

- **服务器**: 39.105.12.124
- **端口**: 8080
- **用户**: u_topn
- **部署目录**: /home/u_topn/TOP_N
- **访问地址**: http://39.105.12.124:8080

### 管理命令

#### 查看服务状态
```bash
ssh u_topn@39.105.12.124
ps aux | grep gunicorn
netstat -tuln | grep 8080
```

#### 查看日志
```bash
tail -f /home/u_topn/TOP_N/logs/gunicorn_error.log
tail -f /home/u_topn/TOP_N/logs/gunicorn_access.log
```

#### 重启服务
```bash
# 停止服务
pkill -9 -f 'gunicorn.*app'

# 启动服务
cd /home/u_topn/TOP_N/backend
nohup python3.14 -m gunicorn --config ../gunicorn_config.py app_factory:app > ../logs/gunicorn.log 2>&1 &
```

#### 快速部署
```bash
cd D:\work\code\TOP_N
python scripts/deploy/deploy_final_correct.py
```

## 🎯 功能模块

### 核心模块

| 模块 | 说明 | 状态 |
|------|------|------|
| 用户认证 | 注册、登录、权限管理 | ✅ 完成 |
| 文件上传 | 支持PDF、Word、TXT | ✅ 完成 |
| AI分析 | 公司信息智能分析 | ✅ 完成 |
| 文章生成 | 批量生成推广文章 | ✅ 完成 |
| 账号管理 | 平台账号配置 | ✅ 完成 |
| 自动发布 | 知乎自动发布 | ✅ 完成 |
| 工作流 | 流程管理和历史 | ✅ 完成 |

### 服务层

- **文件服务**: 文件上传、验证、文本提取
- **AI服务**: 智能分析、文章生成、平台推荐
- **账号服务**: 账号CRUD、密码加密
- **工作流服务**: 流程管理、数据持久化
- **发布服务**: 平台发布、历史记录

## 🔐 安全性

- ✅ 用户密码哈希存储
- ✅ 平台账号密码加密
- ✅ Session安全配置
- ✅ HTTPS支持（推荐）
- ✅ SQL注入防护
- ✅ XSS防护

## 📊 性能指标

- 响应时间: < 200ms (不含AI调用)
- AI分析: 5-10秒
- 文章生成: 10-30秒/篇
- 并发支持: 50+ 用户
- 内存占用: ~130MB

## 🛠️ 开发

### 目录结构

参见 [目录结构索引](DIRECTORY_INDEX.md)

### 开发规范

1. **代码规范**: 遵循PEP 8
2. **分支管理**: Git Flow
3. **提交规范**: Conventional Commits
4. **测试要求**: 覆盖率 > 80%

### 运行测试

```bash
# 运行所有测试
python scripts/test/test_refactored_app.py

# 运行特定测试
python -m unittest tests.test_services
```

## 📦 依赖管理

主要依赖：
- Flask >= 2.0
- Flask-CORS
- requests
- python-docx
- PyPDF2
- SQLAlchemy
- paramiko
- DrissionPage

完整依赖见 [requirements.txt](requirements.txt)

## 🤝 贡献

欢迎贡献代码！请遵循以下步骤：

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📝 更新日志

### v2.0 (2025-12-08)
- ✨ 完成代码重构，采用模块化架构
- ✨ 新增服务层，降低耦合度
- ✨ 新增蓝图系统，优化路由组织
- ✨ 新增知乎自动登录功能
- ✨ 完善文档体系

### v1.0 (2024-12-01)
- 🎉 项目初始版本
- ✨ 基础功能实现

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 👥 团队

- 项目负责人: [Your Name]
- 技术支持: [Support Email]

## 🔗 相关链接

- [项目主页](https://github.com/topn2024/TOP_N)
- [文档中心](https://github.com/topn2024/TOP_N/wiki)
- [问题反馈](https://github.com/topn2024/TOP_N/issues)
- [更新日志](CHANGELOG.md)

## ⚠️ 免责声明

本项目仅供学习和研究使用。使用本项目进行商业推广时，请遵守各平台的服务条款和相关法律法规。

---

**Version**: 2.0
**Last Updated**: 2025-12-08
**Status**: ✅ Production Ready
