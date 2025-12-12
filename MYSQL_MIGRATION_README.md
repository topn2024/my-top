# TOP_N平台 MySQL迁移项目文档

## 📋 项目概述

本项目已完成从localStorage到MySQL数据库的迁移,实现了多用户系统和数据持久化存储。

## ✅ 已完成的工作

### 1. 数据库基础设施 (100%)

#### 创建的文件:
- `backend/models.py` (247行) - SQLAlchemy ORM模型定义
- `backend/auth.py` (135行) - 用户认证模块
- `backend/encryption.py` (116行) - 密码加密工具
- `backend/database.py` (84行) - 数据库连接工具
- `backend/init_db.py` (258行) - 数据库初始化脚本
- `backend/create_admin.py` (64行) - 管理员创建脚本
- `backend/migrate_accounts.py` (152行) - 账号迁移脚本
- `templates/login.html` - 登录/注册页面

#### 数据库表结构:
```
users              - 用户表
├── id            (主键)
├── username      (唯一,索引)
├── email         (唯一,索引)
├── password_hash (pbkdf2:sha256)
└── ...

workflows          - 工作流表
├── id            (主键)
├── user_id       (外键 → users.id)
├── company_name
├── analysis
├── platforms     (JSON)
└── ...

articles           - 文章表
├── id            (主键)
├── workflow_id   (外键 → workflows.id)
├── title
├── content
└── ...

platform_accounts  - 平台账号表
├── id            (主键)
├── user_id       (外键 → users.id)
├── platform
├── username
├── password_encrypted (Fernet加密)
└── ...

publish_history    - 发布历史表
├── id            (主键)
├── article_id    (外键 → articles.id)
├── user_id       (外键 → users.id)
├── platform
└── ...
```

### 2. 后端API更新 (100%)

#### 新增认证端点:
```
POST   /api/auth/register  - 用户注册
POST   /api/auth/login     - 用户登录
POST   /api/auth/logout    - 用户登出
GET    /api/auth/me        - 获取当前用户信息
GET    /login              - 登录页面
```

#### 新增工作流端点:
```
GET    /api/workflow/current - 获取当前工作流
POST   /api/workflow/save    - 保存/更新工作流
GET    /api/workflow/list    - 获取工作流列表
```

#### 更新的现有端点:
```
POST   /api/analyze          - 添加@login_required,保存到数据库
POST   /api/generate_articles - 添加@login_required,保存到数据库
GET    /api/accounts         - 使用数据库,数据隔离
POST   /api/accounts         - 使用数据库,密码加密
DELETE /api/accounts/<id>    - 使用数据库,验证所有权
POST   /api/accounts/<id>/test - 使用数据库,验证所有权
```

### 3. 安全特性 (100%)

- ✅ 用户密码: pbkdf2:sha256哈希 (不可逆)
- ✅ 平台账号密码: Fernet对称加密 (可解密用于自动登录)
- ✅ Session认证: Flask session管理 (24小时有效期)
- ✅ 数据隔离: 每个用户只能访问自己的数据
- ✅ API保护: 所有敏感端点都有@login_required装饰器

## 🚀 部署指南

### 方式一: 在服务器上部署 (推荐)

#### 步骤1: 上传文件到服务器
```bash
# 将以下文件上传到服务器的 /home/u_topn/TOP_N/backend/ 目录:
- models.py
- auth.py
- encryption.py
- database.py
- init_db.py
- create_admin.py
- migrate_accounts.py
- app_with_upload.py (已更新)

# 将login.html上传到 /home/u_topn/TOP_N/templates/ 目录
```

#### 步骤2: SSH连接到服务器并初始化数据库
```bash
ssh u_topn@39.105.12.124

cd /home/u_topn/TOP_N/backend

# 安装依赖
pip3 install pymysql SQLAlchemy cryptography --user

# 初始化数据库
python3 init_db.py

# 创建管理员账号
python3 create_admin.py

# (可选)迁移现有账号数据
python3 migrate_accounts.py

# 重启服务
sudo systemctl restart topn
```

#### 步骤3: 测试
```bash
# 访问登录页面
http://39.105.12.124:8080/login

# 使用管理员账号登录
用户名: admin
密码: TopN@2024
```

### 方式二: 本地开发测试

#### 注意事项:
当前代码配置为连接**服务器本地**的MySQL (localhost:3306),如果要在Windows本地测试,需要:

1. 修改 `backend/models.py` 中的 DATABASE_URL:
```python
# 改为远程连接
DATABASE_URL = 'mysql+pymysql://admin:TopN%40MySQL2024@39.105.12.124:3306/topn_platform?charset=utf8mb4'
```

2. 或者在本地安装MySQL并创建数据库

## 📖 使用说明

### 1. 用户注册和登录

1. 访问 `http://39.105.12.124:8080/login`
2. 新用户点击"注册"标签,填写信息注册
3. 已有用户直接登录

### 2. 默认管理员账号

```
用户名: admin
密码: TopN@2024
邮箱: admin@topn.com
```

**重要**: 首次登录后请修改默认密码!

### 3. API使用示例

#### 用户注册:
```bash
curl -X POST http://39.105.12.124:8080/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123",
    "full_name": "测试用户"
  }'
```

#### 用户登录:
```bash
curl -X POST http://39.105.12.124:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{
    "username": "admin",
    "password": "TopN@2024"
  }'
```

#### 获取当前用户:
```bash
curl http://39.105.12.124:8080/api/auth/me \
  -b cookies.txt
```

#### 保存工作流:
```bash
curl -X POST http://39.105.12.124:8080/api/workflow/save \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "company_name": "测试公司",
    "company_desc": "这是一个测试公司",
    "analysis": "分析内容...",
    "article_count": 3,
    "platforms": ["知乎", "CSDN"],
    "current_step": 2
  }'
```

## 🔧 配置说明

### 环境变量 (可选)

```bash
# Session密钥 (生产环境必须设置)
export TOPN_SECRET_KEY="your-secret-key-here"

# 密码加密密钥 (生产环境必须设置)
export TOPN_ENCRYPTION_KEY="your-encryption-key-here"
```

如果不设置,将使用默认值(仅供开发使用)。

### 数据库连接配置

在 `backend/models.py` 中:
```python
DATABASE_URL = 'mysql+pymysql://admin:TopN%40MySQL2024@localhost:3306/topn_platform?charset=utf8mb4'
```

注意: `@` 符号在URL中需要编码为 `%40`

## 📊 数据库管理

### 查看数据库状态
```bash
mysql -u admin -p'TopN@MySQL2024' -e "USE topn_platform; SHOW TABLES;"
```

### 查看用户列表
```bash
mysql -u admin -p'TopN@MySQL2024' -e "USE topn_platform; SELECT id, username, email, created_at FROM users;"
```

### 查看工作流列表
```bash
mysql -u admin -p'TopN@MySQL2024' -e "USE topn_platform; SELECT id, user_id, company_name, status, created_at FROM workflows;"
```

### 备份数据库
```bash
mysqldump -u admin -p'TopN@MySQL2024' topn_platform > topn_backup_$(date +%Y%m%d).sql
```

### 恢复数据库
```bash
mysql -u admin -p'TopN@MySQL2024' topn_platform < topn_backup_20241207.sql
```

## 🐛 故障排查

### 1. 无法连接数据库

**错误**: `Can't connect to MySQL server`

**解决**:
```bash
# 检查MySQL是否运行
sudo systemctl status mysql

# 检查数据库是否存在
mysql -u admin -p'TopN@MySQL2024' -e "SHOW DATABASES;"

# 重新初始化
python3 backend/init_db.py
```

### 2. 登录失败

**错误**: "用户名或密码错误"

**解决**:
```bash
# 重置admin密码
python3 backend/create_admin.py
```

### 3. Session过期

**现象**: 需要频繁登录

**解决**: 在 `backend/app_with_upload.py` 中调整:
```python
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24小时,可以调大
```

### 4. 密码加密/解密失败

**错误**: "加密失败" 或 "解密失败"

**解决**: 设置统一的加密密钥:
```bash
export TOPN_ENCRYPTION_KEY="固定的32字节密钥"
```

## 🔄 从localStorage迁移

### 当前状态
系统**同时支持**两种模式:
- ✅ 新用户: 使用MySQL数据库
- ✅ 老用户: 仍可使用localStorage (向后兼容)

### 完全迁移步骤 (可选)

如需完全移除localStorage,还需要更新以下前端文件:

1. **更新 `static/state.js`** - 将所有localStorage调用改为API调用
2. **更新 `static/input.js`** - 添加认证检查
3. **更新 `static/analysis.js`** - 使用API加载数据
4. **更新 `static/articles.js`** - 使用API加载文章
5. **更新 `static/publish.js`** - 使用API加载发布历史

这些工作可以根据需要逐步进行。

## 📝 重要注意事项

### 生产环境安全

1. **修改默认密码**:
   - 管理员密码 (admin/TopN@2024)
   - MySQL root密码

2. **设置环境变量**:
   ```bash
   export TOPN_SECRET_KEY="$(openssl rand -base64 32)"
   export TOPN_ENCRYPTION_KEY="$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"
   ```

3. **配置HTTPS**: 生产环境必须使用HTTPS

4. **定期备份数据库**: 建议每天自动备份

5. **监控日志**:
   ```bash
   sudo journalctl -u topn -f
   ```

## 📂 项目文件结构

```
TOP_N/
├── backend/
│   ├── app_with_upload.py    (已更新 - 主应用)
│   ├── models.py             (新增 - 数据模型)
│   ├── auth.py               (新增 - 认证模块)
│   ├── encryption.py         (新增 - 加密工具)
│   ├── database.py           (新增 - 数据库工具)
│   ├── init_db.py            (新增 - 初始化脚本)
│   ├── create_admin.py       (新增 - 创建管理员)
│   └── migrate_accounts.py   (新增 - 迁移账号)
├── templates/
│   ├── login.html            (新增 - 登录页面)
│   ├── input.html            (现有)
│   ├── analysis.html         (现有)
│   ├── articles.html         (现有)
│   └── publish.html          (现有)
├── static/
│   ├── state.js              (现有 - 待更新)
│   └── ...
└── README.md
```

## 🎯 下一步计划

根据需要可以继续完成:

1. ✅ 前端完全迁移到API调用
2. ✅ 添加用户个人资料管理
3. ✅ 添加工作流历史记录查看
4. ✅ 实现数据导出功能
5. ✅ 添加用户权限管理

## 📞 技术支持

如有问题,请检查:
1. 服务器日志: `sudo journalctl -u topn -n 100`
2. MySQL日志: `sudo journalctl -u mysql -n 100`
3. 数据库连接: 确认MySQL服务运行正常

---

**最后更新**: 2024-12-07
**版本**: MySQL Migration v1.0
**状态**: ✅ 核心功能已完成,可正常使用
