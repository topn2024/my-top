# Template ID 修复部署说明

## 问题描述
分析按钮失败的根本原因：Workflow模型缺少`template_id`字段，导致保存工作流时报错。

## 修复内容
1. 在Workflow模型中添加了`template_id`字段
2. 更新了`to_dict()`方法以包含template_id
3. 创建了数据库迁移脚本

## 部署步骤

### 方式一：使用SCP和SSH（推荐）

```bash
# 1. 上传更新的models.py
scp D:\code\TOP_N\backend\models.py u_topn@39.105.12.124:/home/u_topn/TOP_N/backend/

# 2. 上传迁移脚本
scp D:\code\TOP_N\backend\add_template_id_column.py u_topn@39.105.12.124:/home/u_topn/TOP_N/backend/

# 3. SSH连接到服务器
ssh u_topn@39.105.12.124

# 4. 在服务器上执行以下命令
cd /home/u_topn/TOP_N/backend

# 5. 运行迁移脚本
python3 add_template_id_column.py

# 6. 重启Gunicorn
pkill -HUP -f gunicorn

# 7. 测试分析功能
curl -X POST http://localhost:8080/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"company_name":"测试公司","company_desc":"这是一个测试公司","article_count":3}'
```

### 方式二：手动执行SQL（如果迁移脚本有问题）

```bash
# 1. SSH连接到服务器
ssh u_topn@39.105.12.124

# 2. 上传models.py（如果SCP失败，可以手动复制粘贴）
cd /home/u_topn/TOP_N/backend

# 3. 手动添加template_id列
python3 << 'EOF'
from sqlalchemy import text
from models import SessionLocal

session = SessionLocal()
try:
    # 检查列是否存在
    result = session.execute(text("PRAGMA table_info(workflows)"))
    columns = [row[1] for row in result]

    if 'template_id' not in columns:
        print("Adding template_id column...")
        session.execute(text("ALTER TABLE workflows ADD COLUMN template_id VARCHAR(100)"))
        session.commit()
        print("SUCCESS: Column added")
    else:
        print("INFO: Column already exists")
except Exception as e:
    session.rollback()
    print(f"ERROR: {e}")
finally:
    session.close()
EOF

# 4. 重启Gunicorn
pkill -HUP -f gunicorn
```

### 方式三：使用SQLite命令行（最简单）

```bash
# 1. SSH连接到服务器
ssh u_topn@39.105.12.124

# 2. 直接使用SQLite添加列
cd /home/u_topn/TOP_N
sqlite3 data/topn.db << 'EOF'
.schema workflows
ALTER TABLE workflows ADD COLUMN template_id VARCHAR(100);
.schema workflows
.quit
EOF

# 3. 上传models.py（必须）
# 退出SSH，在本地执行：
exit
scp D:\code\TOP_N\backend\models.py u_topn@39.105.12.124:/home/u_topn/TOP_N/backend/

# 4. 重新连接并重启
ssh u_topn@39.105.12.124
pkill -HUP -f gunicorn
```

## 验证修复

在服务器上执行：

```bash
# 检查列是否添加成功
cd /home/u_topn/TOP_N
sqlite3 data/topn.db "PRAGMA table_info(workflows);" | grep template_id

# 检查日志
tail -f logs/all.log

# 测试API
curl -X POST http://localhost:8080/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"company_name":"测试公司","company_desc":"这是一个AI技术公司","article_count":3}'
```

## 已修复的错误链

1. ✅ ModuleNotFoundError in workflow_service.py
2. ✅ AIService initialization error in api.py
3. ✅ API key configuration in config.py
4. ✅ template_id field missing in Workflow model (需要部署)

## 注意事项

- 必须上传更新的`models.py`文件，否则ORM模型不会识别新字段
- 数据库迁移只需执行一次
- 重启Gunicorn使用`pkill -HUP`是优雅重启，不会中断现有连接
- 如果遇到权限问题，可能需要使用`sudo`

## 当前SSH连接问题

目前服务器SSH连接被立即关闭（"Connection closed by remote host"），可能原因：
1. 服务器防火墙/安全组规则更改
2. SSH服务配置问题
3. 连接频率限制（fail2ban等）
4. SSH密钥问题

建议：
- 检查服务器SSH服务状态
- 查看服务器SSH日志：`sudo tail -f /var/log/auth.log`
- 检查fail2ban状态：`sudo fail2ban-client status sshd`
