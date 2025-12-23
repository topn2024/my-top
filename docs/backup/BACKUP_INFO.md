# TOP_N 项目备份信息

## 📦 备份位置

### 本地备份
- **文件**: `backup_local_20251209_234331.tar.gz`
- **大小**: 73MB
- **位置**: `D:\work\code\TOP_N\`
- **创建时间**: 2024-12-09 23:43

### 服务器备份
- **文件**: `TOP_N_backup_20251209_235137.tar.gz`
- **大小**: 3.1MB
- **位置**: `/home/u_topn/backups/`
- **创建时间**: 2024-12-09 23:51
- **服务器**: 39.105.12.124

## 📝 备份内容

### 包含的文件
- ✅ backend/ - 后端Python代码
- ✅ static/ - 静态资源文件（CSS, JS）
- ✅ templates/ - HTML模板文件
- ✅ config.py - 配置文件（含API密钥）
- ✅ 数据库文件
- ✅ 文档和说明文件

### 排除的文件
- ❌ venv/ - Python虚拟环境
- ❌ __pycache__/ - Python缓存
- ❌ *.pyc - 编译文件
- ❌ logs/*.log - 日志文件
- ❌ .git/ - Git仓库
- ❌ node_modules/ - Node依赖

## 🎯 当前版本特性

### 1. 多模型AI支持
**通义千问系列**:
- qwen-plus - 通用场景，平衡性能与成本
- qwen-max - 复杂任务，最强性能
- qwen-turbo - 快速响应，经济实惠

**智谱AI系列** (新增):
- glm-4-plus - 智谱最强模型，复杂推理任务
- glm-4-air - 平衡性能，日常对话
- glm-4-flash - 快速响应，经济实惠

### 2. 用户认证系统
- 用户注册/登录功能
- Session持久化管理
- 密码Werkzeug哈希加密
- 当前用户信息显示

### 3. 发布历史管理
- 独立的 `PublishHistoryManager` 模块
- 分页显示（默认每页10条）
- 统计信息展示（总数/成功/失败）
- 发布失败重试功能
- **自动更新临时发布文章标题**（从知乎获取）

### 4. 知乎自动发布
- 二维码扫码登录
- Cookie持久化存储
- 批量文章发布
- 发布状态追踪

### 5. 工作流管理
- 公司/产品信息分析
- 多维度AI文章生成
- 文章编辑和预览
- 发布到多平台

## 🔧 技术栈

### 后端
- Python 3.x
- Flask (Web框架)
- SQLAlchemy (ORM)
- Selenium (Web自动化)
- Gunicorn (WSGI服务器)

### 前端
- HTML5 / CSS3
- JavaScript (ES6+)
- 模块化架构

### AI服务
- 通义千问 API
- 智谱AI API

### 数据库
- MySQL 8.0

## 📋 数据库结构

### 主要表
- `users` - 用户表
- `workflows` - 工作流表
- `articles` - 文章表
- `publish_history` - 发布历史表

## 🔐 配置信息

### API密钥 (已配置)
- 通义千问: `sk-f0a85d3e56a746509ec435af2446c67a`
- 智谱AI: `d6ac02f8c1f6f443cf81f3dae86fb095.7Qe6KOWcVDlDlqDJ`

### 管理员账号
- 用户名: `admin`
- 密码: `TopN@2024`

### 服务器访问
- 地址: `39.105.12.124`
- 用户: `u_topn`
- 密码: `TopN@2024`
- 端口: 8080

## 🔄 恢复备份

### 本地恢复
```bash
cd D:\work\code\
tar -xzf TOP_N\backup_local_20251209_234331.tar.gz
```

### 服务器恢复
```bash
ssh u_topn@39.105.12.124
cd /home/u_topn
tar -xzf backups/TOP_N_backup_20251209_235137.tar.gz
```

### 恢复后操作
1. 安装依赖: `pip install -r requirements.txt`
2. 配置数据库连接
3. 启动服务: `./start_service.sh`

## 📊 重要文件清单

### 核心配置文件
- `backend/config.py` - 系统配置（API密钥等）
- `start_service.sh` - 服务启动脚本
- `requirements.txt` - Python依赖

### 关键代码文件
- `backend/services/ai_service.py` - AI服务（多模型支持）
- `backend/services/publish_service.py` - 发布服务
- `backend/services/title_updater.py` - 标题更新服务
- `backend/blueprints/api.py` - API路由
- `static/publish_history.js` - 发布历史前端模块
- `static/publish.js` - 发布页面逻辑

## 🎉 最近更新

### 2024-12-09 更新内容
1. ✅ 集成智谱AI三个模型（glm-4-plus, glm-4-air, glm-4-flash）
2. ✅ 配置智谱API密钥并测试通过
3. ✅ 发布页面显示当前登录用户
4. ✅ 发布历史模块化重构（分页支持）
5. ✅ 自动更新临时发布文章标题功能
6. ✅ 修复发布历史数据显示问题（LEFT OUTER JOIN）
7. ✅ 完成本地和服务器双重备份

## 📞 维护建议

1. **定期备份**: 建议每周或重大更新后进行备份
2. **保留策略**: 保留最近3-5个备份版本
3. **测试恢复**: 定期测试备份恢复流程
4. **安全更新**: 定期更新依赖包和安全补丁
5. **日志监控**: 定期检查服务日志

## 📅 下次备份建议时间
- 建议时间: 2024-12-16（一周后）
- 或在重大功能更新前

---
**备份创建时间**: 2024-12-09 23:43 (本地) / 23:51 (服务器)
**版本号**: v1.0 with Zhipu AI Integration
**状态**: ✅ 已测试通过
