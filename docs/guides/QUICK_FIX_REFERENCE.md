# 管理控制台访问问题 - 快速修复参考

## 问题总结

✅ **本地环境**：正常工作
❌ **服务器环境**：返回 401/403 错误

## 根本原因

服务器使用 blueprints 架构，`auth_decorators.py` 中的权限检查过于严格。

## 已修复的文件

```
backend/auth_decorators.py  ← 主要修复文件
```

## 快速部署命令

### 一键部署（自动）

```bash
chmod +x deploy_fix_to_server.sh
./deploy_fix_to_server.sh
```

### 手动部署（3 步）

```bash
# 1. 上传文件
scp backend/auth_decorators.py u_topn@39.105.12.124:/home/u_topn/TOP_N/backend/

# 2. 登录服务器
ssh u_topn@39.105.12.124

# 3. 重启应用
cd /home/u_topn/TOP_N
pkill -9 gunicorn && cd backend && nohup gunicorn -c gunicorn_config.py app:app > ../logs/gunicorn.log 2>&1 &
```

## 验证命令

```bash
# 在服务器上测试
curl -c cookies.txt -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"TopN@2024"}'

curl -b cookies.txt http://localhost:8080/admin
```

## 修复内容

### 修改前
```python
role = getattr(user, 'role', 'user')
if role != ROLE_ADMIN:  # 太严格
    return error
```

### 修改后
```python
role = getattr(user, 'role', 'user')
username = getattr(user, 'username', '')

is_admin = (
    role == ROLE_ADMIN or
    username.lower() in ['admin', 'administrator', 'superuser', 'root']
)

if not is_admin:
    return error
```

## 如果还是不行

### 检查用户角色
```python
# 在服务器上运行 Python
cd /home/u_topn/TOP_N/backend
python3

from models import SessionLocal, User
db = SessionLocal()
admin_user = db.query(User).filter_by(username='admin').first()
print(f"角色: {admin_user.role}")

# 如果不是 'admin'，修复它
admin_user.role = 'admin'
db.commit()
```

### 查看日志
```bash
tail -f /home/u_topn/TOP_N/logs/gunicorn.log
```

## 测试访问

部署后访问：http://39.105.12.124:8080/admin

---

**完成部署后，管理控制台应该可以正常访问！**