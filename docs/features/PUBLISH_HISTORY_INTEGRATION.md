# 发布历史系统整合文档

## 整合概述

完成了新旧两套发布历史系统的整合，统一使用基于SQLAlchemy ORM的新系统。

**整合日期**: 2025-12-11
**执行人**: Claude Code

---

## 旧系统 vs 新系统

### 旧系统（已废弃）

- **数据库**: `backend/publish_history.db` (独立SQLite文件)
- **API**: `backend/publish_history_api.py` (独立API文件)
- **表结构**:
  - 包含完整文章信息 (title, content, word_count)
  - 无用户ID，使用字符串username
  - 字段：id, title, content, platform, account_username, status, article_url, error_message, publish_time, article_type, word_count, publish_user

### 新系统（当前使用）

- **数据库**: `data/topn.db` (统一数据库)
- **模型**: `models.PublishHistory` (ORM模型)
- **API**: `blueprints/api.py:/api/publish_history` (集成到主API)
- **表结构**:
  - 通过article_id关联文章（外键）
  - 使用user_id关联用户（外键）
  - 字段：id, article_id, user_id, platform, status, url, message, published_at

---

## 整合过程

### 1. 分析差异

旧系统和新系统的主要差异：
- 数据库位置不同
- 字段结构不同
- 旧系统冗余存储文章内容，新系统通过外键关联

### 2. 数据迁移

**步骤**:
1. 修改models.py，将PublishHistory.article_id改为nullable=True（支持临时发布）
2. 创建迁移脚本 `migrate_publish_history.py`
3. 从旧数据库读取13条历史记录
4. 转换并写入新数据库

**迁移结果**:
```
✓ 成功迁移: 13 条记录
✓ 跳过重复: 0 条
✓ 新系统总记录: 13 条
```

### 3. 清理旧系统

**删除的文件**:
- `backend/publish_history_api.py` - 旧API文件
- `backend/init_publish_history_db.py` - 旧初始化脚本
- `backend/publish_history.db` - 旧数据库文件（已备份）
- `backend/models.py.bak_publish_history_fix` - 备份文件

**备份位置**:
- `backend/publish_history.db.backup_20251211_*` - 旧数据库备份

**保留的文件**:
- `templates/publish_history.html` - 前端页面
- `static/publish_history.js` - 前端脚本
- `migrate_publish_history.py` - 迁移脚本（留作参考）

### 4. Worker集成

在 `publish_worker.py` 中添加了发布成功后自动保存到PublishHistory的逻辑：

```python
# 保存到发布历史
try:
    db = get_db_session()
    history_record = PublishHistory(
        user_id=task_info['user_id'],
        article_id=task_info.get('article_id'),
        platform=task_info['platform'],
        status='success',
        url=result.get('url'),
        message='发布成功'
    )
    db.add(history_record)
    db.commit()
    task_log.log("✓ 发布历史已保存到数据库")
    db.close()
except Exception as he:
    task_log.log(f"⚠️ 保存发布历史失败: {he}", 'WARN')
```

---

## 新系统架构

### 数据流程

```
用户发布文章
    ↓
API: /api/publish_zhihu_batch
    ↓
TaskQueueManager.create_publish_task()
    ↓
创建 PublishTask 记录
    ↓
RQ Worker执行
    ↓
发布成功
    ↓
创建 PublishHistory 记录 ✓
```

### 数据库关系

```
User (用户表)
  ├─ PublishHistory (发布历史) - user_id
  └─ Article (文章表)
       └─ PublishHistory (发布历史) - article_id (nullable)
```

### API端点

- **获取发布历史**: `GET /api/publish_history?limit=20&platform=zhihu`
- **重试发布**: `POST /api/retry_publish/{history_id}`
- **更新临时标题**: `POST /api/update_temp_titles`

---

## 使用新系统

### 查询发布历史

```python
from models import PublishHistory, get_db_session

db = get_db_session()

# 获取用户的所有发布历史
history = db.query(PublishHistory).filter_by(user_id=1).all()

# 获取最近的成功记录
success_records = db.query(PublishHistory).filter_by(
    user_id=1,
    status='success'
).order_by(PublishHistory.published_at.desc()).limit(10).all()

db.close()
```

### 手动创建发布历史

```python
from models import PublishHistory, get_db_session
from datetime import datetime

db = get_db_session()

record = PublishHistory(
    user_id=1,
    article_id=None,  # 临时发布可以为None
    platform='知乎',
    status='success',
    url='https://zhuanlan.zhihu.com/p/12345',
    message='发布成功',
    published_at=datetime.now()
)

db.add(record)
db.commit()
db.close()
```

---

## 优势

### 新系统相比旧系统的优势

1. **统一数据库**: 所有数据在一个地方，便于管理和查询
2. **外键关联**: 通过article_id和user_id建立关系，数据规范化
3. **ORM支持**: 使用SQLAlchemy ORM，代码更简洁、类型安全
4. **自动化**: Worker发布成功后自动保存，无需手动调用
5. **扩展性**: 易于添加新平台、新字段

### 数据一致性

- PublishTask表记录任务状态（pending, queued, running, success, failed）
- PublishHistory表记录最终结果（success, failed）
- 两表独立但互补，PublishHistory是PublishTask成功后的结果快照

---

## 验证

### 检查迁移结果

```bash
cd /home/u_topn/TOP_N
python3 << 'EOF'
import sys
sys.path.insert(0, 'backend')
from models import PublishHistory, get_db_session

db = get_db_session()
print(f'总记录数: {db.query(PublishHistory).count()}')

# 按状态统计
from sqlalchemy import func
stats = db.query(
    PublishHistory.status,
    func.count(PublishHistory.id)
).group_by(PublishHistory.status).all()

print('\n按状态统计:')
for status, count in stats:
    print(f'  {status}: {count}')

db.close()
EOF
```

预期输出：
```
总记录数: 13

按状态统计:
  success: 5
  failed: 8
```

### 访问前端页面

打开浏览器访问：`http://39.105.12.124:8080/publish_history`

应该能看到：
- ✓ 13条历史记录（迁移的旧数据）
- ✓ 包含状态、平台、URL、时间等信息
- ✓ 可以按状态筛选

---

## 注意事项

### article_id可以为NULL

新系统支持临时发布（不通过Article表的文章），此时article_id为NULL。这是为了兼容：
1. 旧系统迁移的数据（没有article_id）
2. 未来可能的临时发布功能

### 时区问题

PublishHistory.published_at使用TIMESTAMP类型，默认为服务器时区（CST）。

### 备份恢复

如需恢复旧数据，备份文件位于：
```
/home/u_topn/TOP_N/backend/publish_history.db.backup_20251211_*
```

---

## 迁移脚本

完整的迁移脚本保存在 `migrate_publish_history.py`，可重复运行（会跳过已存在的记录）。

---

## 故障排查

### 问题：前端看不到发布历史

**检查步骤**:
1. 确认数据库中有记录：
   ```bash
   sqlite3 data/topn.db "SELECT COUNT(*) FROM publish_history"
   ```

2. 检查API是否正常：
   ```bash
   curl -X GET 'http://39.105.12.124:8080/api/publish_history' \
     -H 'Cookie: session=你的session'
   ```

3. 查看浏览器控制台是否有JS错误

### 问题：新发布的文章没有保存到历史

**检查步骤**:
1. 查看worker日志：
   ```bash
   tail -50 /home/u_topn/TOP_N/logs/worker-1.log
   ```

2. 确认是否有"✓ 发布历史已保存到数据库"日志

3. 检查publish_worker.py是否导入了PublishHistory

---

## 总结

新旧系统整合已完成，现在使用统一的发布历史系统：

✅ **数据库**: `data/topn.db` (SQLite)
✅ **模型**: `models.PublishHistory` (ORM)
✅ **API**: `/api/publish_history` (集成到主API)
✅ **前端**: `publish_history.html` + `publish_history.js`
✅ **自动保存**: Worker发布成功后自动创建记录
✅ **历史数据**: 13条旧记录已成功迁移

系统更加统一、简洁、易于维护！
