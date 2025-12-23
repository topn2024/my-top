# 配置管理指南

## 配置文件概览

### 主配置文件
- `backend/config.py` - 应用配置类
- `.env` - 环境变量（不提交到Git）
- `.env.example` - 环境变量示例（已创建）

## 配置改进

### 已完成
- ✅ 创建 `.env.example` 示例文件
- ✅ 文档化所有配置项
- ✅ 区分开发/生产环境

### 当前配置已经相对完善
`backend/config.py` 已经实现了：
- ✅ 环境变量支持
- ✅ 多环境配置（开发/生产/测试）
- ✅ 配置类继承
- ✅ 目录自动创建

## 安全建议

### 敏感信息处理
```python
# ❌ 不要硬编码
ZHIPU_API_KEY = 'd6ac02f8c1f6f443...'

# ✅ 使用环境变量
ZHIPU_API_KEY = os.environ.get('ZHIPU_API_KEY', '')
```

### Git忽略
确保 `.gitignore` 包含：
```
.env
*.db
__pycache__/
*.pyc
```

## 使用方法

### 1. 复制示例配置
```bash
cp .env.example .env
```

### 2. 编辑配置
```bash
# 编辑 .env 文件，填入实际值
nano .env
```

### 3. 应用配置
```python
from config import get_config

config = get_config()  # 自动根据FLASK_ENV加载
app.config.from_object(config)
```

## 配置项说明

### 必需配置
- `SECRET_KEY` - Flask密钥（生产必须更改）
- `ZHIPU_API_KEY` 或 `QIANWEN_API_KEY` - AI服务密钥

### 可选配置
- `DATABASE_URL` - 数据库连接（默认SQLite）
- `LOG_LEVEL` - 日志级别（默认INFO）
- `PORT` - 端口号（默认5000）

## 配置验证

### 检查配置
```python
from config import get_config

config = get_config()
config.init_app()  # 创建必要目录

# 验证关键配置
assert config.SECRET_KEY != 'default-secret-key'
assert config.ZHIPU_API_KEY != ''
```

## 结论

- ✅ 配置系统已经完善
- ✅ 环境变量示例已创建
- ✅ 文档已完善
- ✅ 最佳实践已应用

**状态**: 配置管理已达标，标记完成
