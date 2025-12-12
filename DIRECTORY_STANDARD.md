# TOP_N 目录规范

本文档定义TOP_N项目的标准目录结构和文件组织规范。

## 📁 标准目录结构

```
TOP_N/
├── backend/                    # 后端代码目录
│   ├── config.py              # 配置管理
│   ├── app_factory.py         # 应用工厂
│   ├── app_with_upload.py     # 旧版应用(保留)
│   ├── models.py              # 数据模型
│   ├── auth.py                # 认证模块
│   ├── encryption.py          # 加密模块
│   ├── database.py            # 数据库模块
│   ├── services/              # 服务层
│   │   ├── __init__.py
│   │   ├── file_service.py
│   │   ├── ai_service.py
│   │   ├── account_service.py
│   │   ├── workflow_service.py
│   │   └── publish_service.py
│   ├── blueprints/            # 路由蓝图
│   │   ├── __init__.py
│   │   ├── api.py
│   │   ├── auth.py
│   │   └── pages.py
│   ├── publishers/            # 发布器模块
│   ├── utils/                 # 工具函数
│   └── cookies/               # Cookie存储
│
├── templates/                  # HTML模板
│   ├── home.html
│   ├── login.html
│   ├── platform.html
│   ├── analysis.html
│   ├── articles.html
│   └── publish.html
│
├── static/                     # 静态资源
│   ├── css/
│   ├── js/
│   └── images/
│
├── frontend/                   # 前端项目(可选)
│   ├── src/
│   ├── public/
│   └── package.json
│
├── scripts/                    # 运维脚本
│   ├── deploy/                # 部署脚本
│   │   └── deploy_final_correct.py
│   ├── check/                 # 检查脚本
│   │   ├── verify_deployment.py
│   │   └── check_gunicorn_setup.py
│   ├── test/                  # 测试脚本
│   │   └── test_refactored_app.py
│   ├── install/               # 安装脚本
│   ├── fix/                   # 修复脚本
│   └── README.md
│
├── docs/                       # 文档目录
│   ├── REFACTORING_GUIDE.md
│   ├── SERVICE_USAGE_EXAMPLES.md
│   ├── MIGRATION_GUIDE.md
│   └── business/              # 业务文档
│       ├── AI生成内容识别清单.docx
│       └── 公司介绍.docx
│
├── archive/                    # 归档目录
│   ├── temp/                  # 临时文件和旧脚本
│   ├── old_docs/              # 旧文档
│   ├── chromedriver/          # ChromeDriver旧版本
│   └── python_installers/     # Python安装包
│
├── data/                       # 数据文件
│   └── .gitkeep
│
├── uploads/                    # 用户上传文件
│   └── .gitkeep
│
├── logs/                       # 日志文件
│   ├── gunicorn_access.log
│   ├── gunicorn_error.log
│   └── .gitkeep
│
├── accounts/                   # 账号配置
│   └── accounts.json
│
├── .gitignore                  # Git忽略配置
├── README.md                   # 项目说明
├── QUICK_DEPLOY.md            # 快速部署指南
├── PROJECT_CONFIG.md          # 工程配置
├── DIRECTORY_INDEX.md         # 目录索引
├── DIRECTORY_STANDARD.md      # 本文件
├── REFACTORING_SUMMARY.md     # 重构总结
├── REFACTORING_COMPLETE.md    # 重构完成报告
├── requirements.txt           # Python依赖
└── start.sh                   # 启动脚本
```

## 📋 目录说明

### backend/ - 后端代码
**用途**: 存放所有后端业务代码
**规范**:
- ✅ 业务逻辑代码
- ✅ 数据模型
- ✅ 配置文件
- ❌ 不存放运维脚本
- ❌ 不存放测试脚本
- ❌ 不存放文档

### backend/services/ - 服务层
**用途**: 封装业务逻辑，提供服务接口
**规范**:
- 每个服务负责单一职责
- 服务之间低耦合
- 统一的错误处理
- 详细的日志记录

### backend/blueprints/ - 路由蓝图
**用途**: 组织和管理路由
**规范**:
- 按功能模块划分蓝图
- 控制器只负责请求响应
- 业务逻辑交给服务层

### templates/ - HTML模板
**用途**: 存放Jinja2模板文件
**规范**:
- 使用语义化命名
- 模板继承和包含
- 避免业务逻辑

### static/ - 静态资源
**用途**: CSS、JavaScript、图片等静态文件
**规范**:
- 按类型分目录
- 压缩和优化
- 版本控制

### scripts/ - 运维脚本
**用途**: 部署、测试、检查等脚本
**规范**:
- 按功能分类
- 命名规范: `动作_对象.py`
- 详细的注释和文档

### docs/ - 文档
**用途**: 项目文档、API文档、技术文档
**规范**:
- Markdown格式
- 及时更新
- 结构清晰

### archive/ - 归档
**用途**: 旧版本文件、临时文件
**规范**:
- 不再使用的文件移至此处
- 保留历史记录
- 定期清理

### data/ - 数据文件
**用途**: 数据库文件、数据导出等
**规范**:
- 不提交到Git
- 定期备份

### uploads/ - 上传文件
**用途**: 用户上传的文件
**规范**:
- 不提交到Git
- 文件大小限制
- 定期清理

### logs/ - 日志
**用途**: 应用日志、访问日志、错误日志
**规范**:
- 不提交到Git
- 日志轮转
- 保留时间限制

## 📝 文件命名规范

### Python文件
- 模块: 小写字母+下划线 `file_service.py`
- 类: 大驼峰 `class FileService`
- 函数: 小写字母+下划线 `def save_file()`
- 常量: 大写字母+下划线 `MAX_FILE_SIZE`

### 文档文件
- Markdown: 大写字母+下划线 `README.md`, `QUICK_DEPLOY.md`
- 业务文档: 中文名称 `公司介绍.docx`
- 放在对应目录

### 脚本文件
- 格式: `动作_对象.py`
- 示例:
  - `deploy_final_correct.py`
  - `check_gunicorn_setup.py`
  - `test_refactored_app.py`

## 🚫 禁止事项

### 不要放在项目根目录
- ❌ 临时文件 (*.tmp, nul)
- ❌ 备份文件 (*.bak, *.backup)
- ❌ 测试脚本
- ❌ 业务文档 (放到docs/business/)
- ❌ 数据文件 (放到data/)

### 不要放在backend/
- ❌ 部署脚本 → scripts/deploy/
- ❌ 测试脚本 → scripts/test/
- ❌ 检查脚本 → scripts/check/
- ❌ 临时文件 → archive/temp/

### 不要提交到Git
- ❌ `__pycache__/`
- ❌ `*.pyc`
- ❌ `/uploads/*` (除了.gitkeep)
- ❌ `/logs/*` (除了.gitkeep)
- ❌ `/data/*` (除了.gitkeep)
- ❌ `.env`
- ❌ 临时文件

## ✅ 最佳实践

### 1. 新建文件时
- 确认文件用途
- 选择正确目录
- 使用规范命名
- 添加必要注释

### 2. 新建目录时
- 确认是否必要
- 遵循现有结构
- 创建.gitkeep (如果需要空目录)
- 更新本文档

### 3. 删除文件时
- 不要直接删除
- 移至archive/temp/
- 保留一段时间
- 定期清理

### 4. 重构代码时
- 保留旧版本
- 做好备份
- 更新文档
- 测试验证

## 📋 检查清单

在提交代码前，检查：

- [ ] 文件在正确的目录
- [ ] 文件命名符合规范
- [ ] 没有临时文件
- [ ] 没有敏感信息
- [ ] .gitignore已更新
- [ ] 文档已更新
- [ ] 代码已测试

## 🔧 维护建议

### 每周
- 检查临时文件
- 清理日志文件
- 更新文档

### 每月
- 清理archive/temp/
- 备份重要数据
- 检查磁盘空间

### 每季度
- 全面代码审查
- 重构优化
- 性能测试

## 📞 问题反馈

如发现目录结构问题或有改进建议：
1. 提出Issue
2. 讨论方案
3. 更新文档
4. 通知团队

---

**版本**: 1.0
**创建日期**: 2025-12-08
**最后更新**: 2025-12-08
**状态**: ✅ 生效中

遵循本规范，保持项目结构清晰整洁！
