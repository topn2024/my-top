# 发布任务卡住问题总结 (2025-12-10)

## 问题现状

### 发现的问题
1. ✅ **已修复**: RQ Worker通配符队列不工作
2. ⚠️ **部分修复**: MySQL连接超时
3. ⚠️ **待处理**: 知乎Cookie已过期

### 当前数据库状态
```
总任务: 27
queued: 0
running: 0  (已清理)
success: 0
failed: 27  (所有任务都失败了)
```

## 已完成的修复

### 1. RQ Worker队列配置 ✅

**问题**: Worker监听 `user:*` 通配符，但RQ不支持通配符

**修复**:
```bash
# /home/u_topn/TOP_N/backend/start_workers.sh
rq worker default user:1 user:2 user:3 user:4 user:5
```

**验证**: Worker成功从 `user:1` 队列取出任务并执行

### 2. 清理卡住的任务 ✅

**操作**: 将3个停留在 `running` 状态的任务标记为 `failed`

**原因**: MySQL连接超时导致无法更新最终状态

**错误信息**:
```
MySQL连接超时导致状态更新失败。已修复数据库配置，请重新发布。
```

### 3. 日志级别修改为DEBUG ✅

**文件**: `/home/u_topn/TOP_N/backend/config.py`

**修改**:
```python
# 基础配置
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')

# 生产环境配置
class ProductionConfig(Config):
    LOG_LEVEL = 'DEBUG'
```

**重启**: Gunicorn + RQ Workers 已重启

## 待解决的问题

### 问题A: MySQL连接超时（高优先级）

**现象**:
```
(pymysql.err.OperationalError) (2013, 'Lost connection to MySQL server during query')
```

**根本原因**:
- Worker在整个发布过程中持有同一个数据库Session
- 发布操作耗时较长（6秒+浏览器自动化）
- Session中的MySQL连接在此期间超时

**当前配置** (models.py):
```python
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    pool_pre_ping=True,  # ✓ 已配置，但未生效
    echo=False
)
```

**为什么pool_pre_ping未生效?**

`pool_pre_ping=True` 只在**从连接池获取连接时**测试连接。

但Worker的问题是：
1. 从连接池获取连接 ✓ (此时连接是好的)
2. 更新任务状态为 `running` ✓
3. 执行发布操作 (耗时6秒+) ← 期间持有连接
4. 更新任务进度为90% ✗ (连接已超时，这里失败)

**解决方案**:

#### 方案1: 修改Worker不长时间持有Session (推荐)

修改 `backend/services/publish_worker.py`:

```python
def execute_publish_task(task_db_id: int) -> Dict:
    # 第1阶段: 获取任务信息
    db = get_db_session()
    try:
        task = db.query(PublishTask).filter(...).first()
        task.status = 'running'
        task.started_at = datetime.now()
        db.commit()

        # 保存必要信息到变量
        task_data = {
            'task_id': task.task_id,
            'user_id': task.user_id,
            'article_title': task.article_title,
            'article_content': task.article_content,
            'platform': task.platform
        }
    finally:
        db.close()  # ← 立即关闭

    # 第2阶段: 执行发布 (不持有数据库连接)
    try:
        result = post_article_to_zhihu(
            username=username,
            title=task_data['article_title'],
            content=task_data['article_content'],
            ...
        )
    except Exception as e:
        result = {'success': False, 'error': str(e)}

    # 第3阶段: 更新最终结果 (重新获取Session)
    db = get_db_session()
    try:
        task = db.query(PublishTask).filter(
            PublishTask.id == task_db_id
        ).first()

        if result['success']:
            task.status = 'success'
            task.result_url = result['url']
        else:
            task.status = 'failed'
            task.error_message = result['error']

        task.completed_at = datetime.now()
        db.commit()
    finally:
        db.close()
        rate_limiter.release(task_data['user_id'])
```

#### 方案2: 增加数据库重连重试机制 (备选)

```python
def update_task_status_with_retry(task_id, updates, max_retries=3):
    for attempt in range(max_retries):
        db = get_db_session()
        try:
            task = db.query(PublishTask).filter(...).first()
            for key, val in updates.items():
                setattr(task, key, val)
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

### 问题B: 知乎Cookie已过期（中优先级）

**现象**:
```
Cookie登录失败或Cookie不存在
```

**影响**:
- 无法使用保存的Cookie登录知乎
- 所有发布任务都会失败

**解决方案**:

1. **用户重新登录** (推荐)
   - 访问: http://39.105.12.124:8080/account/manage
   - 重新登录知乎账号
   - 系统自动保存新Cookie

2. **确保密码登录可用** (备选)
   - 检查数据库中是否有加密的密码
   - `zhihu_auto_post_enhanced.py` 会在Cookie失效时自动使用密码登录

3. **修改Cookie有效期** (长期)
   - 检查知乎Cookie的过期时间
   - 考虑定期刷新Cookie机制

## 系统当前状态

### 服务状态
```
✅ Redis:      运行正常
✅ Gunicorn:   6个进程 (1 master + 4 workers)
✅ RQ Worker:  4个进程，监听 default, user:1-5
✅ 日志级别:   DEBUG
```

### 队列状态
```
✅ user:1: 0个任务
✅ user:2: 0个任务
✅ user:3: 0个任务
✅ user:4: 0个任务
✅ user:5: 0个任务
```

### 任务统计
```
总任务: 27
- pending: 0
- queued: 0
- running: 0
- success: 0
- failed: 27
```

**所有任务失败原因**:
1. 18个: RQ Worker重启导致任务丢失
2. 6个: RQ Worker重启导致任务丢失
3. 3个: MySQL连接超时

## 建议的下一步操作

### 立即操作（现在）

1. ✅ **清理卡住的任务** - 已完成

2. ⏭️ **修复Worker Session管理** - 待实施
   ```bash
   # 修改 publish_worker.py
   # 不长时间持有Session
   ```

3. ⏭️ **重启Worker使修复生效**
   ```bash
   ssh u_topn@39.105.12.124 "bash /home/u_topn/TOP_N/backend/start_workers.sh"
   ```

### 短期操作（今天）

4. ⏭️ **用户重新登录知乎**
   - 通知用户访问账号管理页面
   - 重新登录知乎
   - 保存新Cookie

5. ⏭️ **测试完整发布流程**
   - 创建一篇测试文章
   - 发布到知乎
   - 验证从 pending → queued → running → success 完整流程

### 长期优化（本周）

6. **添加监控告警**
   - 监控running状态任务超过5分钟自动告警
   - 监控MySQL连接池状态
   - 监控Cookie有效期

7. **优化发布流程**
   - 减少单次发布操作时间
   - 考虑分阶段提交进度（不在发布过程中更新）

8. **完善错误处理**
   - 所有数据库操作添加重试机制
   - 更友好的错误提示

## 核心问题总结

### 为什么任务会卡住?

```
任务创建 → 入队 (queued) → Worker取出任务 → 更新状态 (running)
                                          ↓
                                    执行发布 (6秒+)
                                          ↓
                                    更新进度90% ← MySQL连接已超时!
                                          ↓
                                    ❌ 抛出异常
                                          ↓
                                    RQ标记Job OK (忽略异常)
                                          ↓
                                    数据库状态未更新
                                          ↓
                                    任务永远停留在 running
```

### 关键修复点

1. **Worker队列配置**: `user:*` → `user:1 user:2 user:3 user:4 user:5`
2. **Session管理**: 分段获取Session，不在发布过程中长时间持有
3. **Cookie管理**: 用户重新登录或确保密码登录可用

## 相关文档

- `WORKER_ISSUE_FINAL_SUMMARY.md` - Worker问题完整诊断
- `SERVER_WORKER_FIX_REPORT.md` - 服务器Worker修复报告
- `SERVER_DEBUG_LOG_ENABLED.md` - DEBUG日志启用报告
- `PUBLISH_STUCK_DIAGNOSIS.md` - 发布卡住详细诊断
- `ISSUE_SUMMARY_20251210.md` - 本文档

---

**报告时间**: 2025-12-10 23:05
**问题状态**: 部分修复，待完成Worker Session管理优化
**下一步**: 修改 publish_worker.py 不长时间持有数据库Session
