# 发布任务卡住问题诊断报告

## 问题描述
用户反馈：发布文章的自动化任务又卡住了

## 诊断结果

### 问题1: RQ Worker队列通配符不工作 ✅ 已修复

**现象**:
- 任务入队到 `user:1` 队列
- Worker监听 `user:*` （字面量）
- 任务无法被处理，停留在 `queued` 状态

**根本原因**:
RQ不支持队列名通配符。`user:*` 被当作字面量队列名，而不是匹配模式。

**修复方案**:
```bash
# 修改前
rq worker default user:*

# 修改后
rq worker default user:1 user:2 user:3 user:4 user:5
```

**修复文件**: `/home/u_topn/TOP_N/backend/start_workers.sh`

**验证结果**: ✅ Worker成功从 `user:1` 队列取出任务并开始执行

---

### 问题2: MySQL连接丢失 ⚠️ 待修复

**现象**:
```
sqlalchemy.exc.OperationalError: (pymysql.err.OperationalError)
(2013, 'Lost connection to MySQL server during query')
```

**发生位置**:
- `publish_worker.py` 更新任务进度到90%时
- 发布过程耗时较长（6秒+），MySQL连接超时

**影响**:
- Worker无法更新任务状态为 `success` 或 `failed`
- 任务永远停留在 `running` 状态
- RQ显示 "Job OK"，但数据库记录未更新

**当前卡住的任务**:
```
[040e36df] running  月栖科技：AI智能体的"领航者"...
[5d2571b8] running  月栖科技：AI智能体的"黑马"...
[3ffdd347] running  月栖科技：AI智能体的"领航者"...
```

---

### 问题3: 知乎Cookie已过期 ⚠️ 待处理

**现象**:
```
Cookie登录失败或Cookie不存在
```

**影响**:
- 无法使用Cookie登录知乎
- 需要重新登录并保存Cookie
- 或使用密码登录作为备选

---

## 问题根源分析

### MySQL连接超时原因

1. **默认超时设置过短**
   - MySQL默认 `wait_timeout` = 8小时
   - 但连接池可能有更短的超时时间
   - 发布任务执行时间可能超过连接超时

2. **数据库连接池配置**
   ```python
   # models.py 中的数据库引擎配置
   engine = create_engine(
       DATABASE_URL,
       poolclass=QueuePool,
       pool_size=5,
       max_overflow=10,
       pool_recycle=3600  # ← 可能需要调整
   )
   ```

3. **Session管理问题**
   - Worker长时间持有Session
   - 中途执行耗时操作（浏览器自动化）
   - Session中的连接超时

## 修复方案

### 方案A: 修复MySQL连接问题（推荐）

#### 1. 优化数据库连接池配置

修改 `backend/models.py`:
```python
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,           # 增加连接池大小
    max_overflow=20,        # 增加溢出连接数
    pool_recycle=1800,      # 30分钟回收连接
    pool_pre_ping=True,     # ← 关键：执行前ping测试连接
    pool_timeout=30,
    echo=False
)
```

**pool_pre_ping=True** 的作用：
- 每次从连接池取出连接前，先ping测试
- 如果连接已断开，自动重新连接
- 避免使用已失效的连接

#### 2. 修改Worker重新获取Session

修改 `backend/services/publish_worker.py`:
```python
def execute_publish_task(task_db_id: int) -> Dict:
    # 不要在开头获取Session并持有整个过程
    # 而是在需要时临时获取

    # 开始时获取任务信息
    db = get_db_session()
    try:
        task = db.query(PublishTask).filter(...).first()
        # 读取必要信息
        task_data = {
            'task_id': task.task_id,
            'user_id': task.user_id,
            'article_title': task.article_title,
            'article_content': task.article_content,
            'platform': task.platform
        }
    finally:
        db.close()  # ← 立即关闭

    # 执行耗时的发布操作（不持有数据库连接）
    result = post_article_to_zhihu(...)

    # 完成后重新获取Session更新结果
    db = get_db_session()
    try:
        task = db.query(PublishTask).filter(...).first()
        task.status = 'success'
        task.result_url = result['url']
        db.commit()
    finally:
        db.close()
```

#### 3. 添加数据库重连机制

```python
from sqlalchemy.exc import OperationalError

def update_task_with_retry(task_id, updates, max_retries=3):
    """带重试的任务更新"""
    for attempt in range(max_retries):
        db = get_db_session()
        try:
            task = db.query(PublishTask).filter(...).first()
            for key, value in updates.items():
                setattr(task, key, value)
            db.commit()
            return True
        except OperationalError as e:
            if '2013' in str(e):  # Lost connection
                db.rollback()
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
            raise
        finally:
            db.close()
    return False
```

### 方案B: 清理当前卡住的任务（临时）

```bash
ssh u_topn@39.105.12.124 "cd /home/u_topn/TOP_N/backend && python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')
from models import PublishTask, get_db_session
from datetime import datetime

db = get_db_session()
try:
    # 找到所有running状态的任务
    running_tasks = db.query(PublishTask).filter(
        PublishTask.status == 'running'
    ).all()

    print(f'找到 {len(running_tasks)} 个running状态的任务')

    for task in running_tasks:
        print(f'重置任务: [{task.task_id[:8]}] {task.article_title[:40]}')
        task.status = 'failed'
        task.error_message = 'MySQL连接超时导致状态更新失败，请修复数据库配置后重试'
        task.completed_at = datetime.now()

    db.commit()
    print(f'✓ 已重置 {len(running_tasks)} 个任务')
finally:
    db.close()
PYEOF
"
```

### 方案C: 修复知乎Cookie问题

#### 选项1: 重新登录获取Cookie

访问系统管理界面，重新登录知乎账号：
```
http://39.105.12.124:8080/account/manage
```

#### 选项2: 配置密码登录备选

确保数据库中有密码信息：
```sql
SELECT id, username, password_encrypted
FROM platform_accounts
WHERE platform = '知乎' AND user_id = 1;
```

## 详细执行日志

### Worker-1日志片段
```
22:57:32 user:1: services.publish_worker.execute_publish_task(task_db_id=25)
Cookie登录失败或Cookie不存在
任务执行失败: (pymysql.err.OperationalError) (2013, 'Lost connection to MySQL server during query')
[SQL: UPDATE publish_tasks SET progress=90 WHERE id = 25]

22:57:32 Successfully completed ... job in 0:00:06.245991s on worker worker-1
22:57:32 user:1: Job OK
```

**分析**:
- RQ认为Job执行完成（Job OK）
- 但Python代码抛出异常（MySQL连接丢失）
- 异常发生在finally块中，被RQ捕获但任务仍标记为完成
- 数据库状态未更新

### 当前系统状态

```
✅ Redis: 运行正常
✅ Worker进程: 4个运行中
✅ Worker队列: 正确监听 user:1, user:2, user:3, user:4, user:5
⚠️  MySQL连接: 频繁超时
⚠️  知乎Cookie: 已过期
❌ 卡住任务: 3个永远处于running状态
```

## 推荐修复顺序

### 立即处理（紧急）

1. **清理卡住的任务** (方案B)
   ```bash
   # 将3个running任务标记为failed
   ssh u_topn@39.105.12.124 "cd /home/u_topn/TOP_N/backend && python3 ..."
   ```

2. **修复MySQL连接池配置** (方案A.1)
   ```python
   # 添加 pool_pre_ping=True
   vim /home/u_topn/TOP_N/backend/models.py
   ```

3. **重启应用和Worker**
   ```bash
   # 重启使配置生效
   pkill -f gunicorn && pkill -f 'rq worker'
   # 重新启动...
   ```

### 短期优化（24小时内）

4. **重构Worker Session管理** (方案A.2)
   - 分段获取Session
   - 不在发布过程中长时间持有连接

5. **添加数据库重连机制** (方案A.3)
   - 捕获OperationalError
   - 自动重试3次

### 长期改进（本周内）

6. **修复知乎Cookie问题** (方案C)
   - 用户重新登录
   - 或确保密码登录可用

7. **添加监控告警**
   - 监控running状态任务数量
   - 超过阈值自动告警

8. **优化发布流程**
   - 考虑将发布过程异步化
   - 减少单个任务执行时间

## 快速命令

### 查看当前状态
```bash
# 检查running任务
ssh u_topn@39.105.12.124 "cd /home/u_topn/TOP_N/backend && python3 -c '
import sys; sys.path.insert(0, \".\")
from models import PublishTask, get_db_session
db = get_db_session()
tasks = db.query(PublishTask).filter(PublishTask.status == \"running\").all()
print(f\"Running任务: {len(tasks)}\")
for t in tasks: print(f\"  [{t.task_id[:8]}] {t.article_title[:40]}\")
db.close()
'"

# 检查Worker日志
ssh u_topn@39.105.12.124 "tail -20 /home/u_topn/TOP_N/logs/worker-1.log"

# 检查MySQL连接
ssh u_topn@39.105.12.124 "mysql -u topn_user -p -e 'SHOW VARIABLES LIKE \"wait_timeout\";'"
```

### 清理running任务
```bash
ssh u_topn@39.105.12.124 "cd /home/u_topn/TOP_N/backend && python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')
from models import PublishTask, get_db_session
from datetime import datetime

db = get_db_session()
running_tasks = db.query(PublishTask).filter(PublishTask.status == 'running').all()
for task in running_tasks:
    task.status = 'failed'
    task.error_message = 'MySQL连接超时，请重试'
    task.completed_at = datetime.now()
db.commit()
print(f'清理了 {len(running_tasks)} 个running任务')
db.close()
PYEOF
"
```

---

**诊断时间**: 2025-12-10 23:00
**诊断人员**: Claude Code
**问题等级**: P1 - 高优先级
**影响范围**: 所有发布任务
**建议修复时间**: 立即处理（1小时内）
