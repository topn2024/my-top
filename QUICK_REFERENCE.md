# 发布系统快速参考

## 系统状态检查

### 快速诊断命令

```bash
# 1. 检查所有服务
ssh u_topn@39.105.12.124 "
echo '=== Redis ==='
redis-cli ping

echo ''
echo '=== Gunicorn ==='
ps aux | grep 'gunicorn.*app_factory' | grep -v grep | wc -l
echo '个进程'

echo ''
echo '=== RQ Worker ==='
ps aux | grep 'rq worker' | grep -v grep | wc -l
echo '个进程'

echo ''
echo '=== 任务状态 ==='
cd /home/u_topn/TOP_N/backend && python3 -c '
import sys; sys.path.insert(0, \".\")
from models import PublishTask, get_db_session
db = get_db_session()
for status in [\"pending\", \"queued\", \"running\", \"success\", \"failed\"]:
    count = db.query(PublishTask).filter(PublishTask.status == status).count()
    print(f\"{status}: {count}\")
db.close()
'
"
```

### 查看日志

```bash
# Worker日志
ssh u_topn@39.105.12.124 "tail -f /home/u_topn/TOP_N/logs/worker-1.log"

# 应用日志
ssh u_topn@39.105.12.124 "tail -f /home/u_topn/TOP_N/logs/error.log"

# 搜索错误
ssh u_topn@39.105.12.124 "grep -i error /home/u_topn/TOP_N/logs/worker-1.log | tail -20"
```

## 常见问题处理

### 问题1: 任务卡在queued

**症状**: 任务一直是queued状态，不变为running

**诊断**:
```bash
# 检查Worker是否运行
ssh u_topn@39.105.12.124 "ps aux | grep 'rq worker' | grep -v grep"

# 检查Redis队列
ssh u_topn@39.105.12.124 "cd /home/u_topn/TOP_N/backend && python3 -c '
import redis
from rq import Queue
r = redis.Redis()
q = Queue(\"user:1\", connection=r)
print(f\"队列长度: {len(q)}\")
'"
```

**解决**:
```bash
# 重启Worker
ssh u_topn@39.105.12.124 "bash /home/u_topn/TOP_N/backend/start_workers.sh"
```

### 问题2: 任务卡在running

**症状**: 任务长时间处于running状态

**诊断**:
```bash
# 查看Worker日志
ssh u_topn@39.105.12.124 "tail -100 /home/u_topn/TOP_N/logs/worker-*.log | grep -A 10 'running'"
```

**解决**:
```bash
# 如果确认任务已卡死，清理它
ssh u_topn@39.105.12.124 "cd /home/u_topn/TOP_N/backend && python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')
from models import PublishTask, get_db_session
from datetime import datetime

db = get_db_session()
tasks = db.query(PublishTask).filter(PublishTask.status == 'running').all()
for t in tasks:
    t.status = 'failed'
    t.error_message = '任务超时，已手动清理'
    t.completed_at = datetime.now()
db.commit()
print(f'清理了 {len(tasks)} 个任务')
db.close()
PYEOF
"
```

### 问题3: MySQL连接失败

**症状**: 日志显示"Lost connection to MySQL server"

**诊断**:
```bash
# 检查MySQL服务
ssh u_topn@39.105.12.124 "systemctl status mysql"

# 检查连接数
ssh u_topn@39.105.12.124 "mysql -u topn_user -p -e 'SHOW STATUS LIKE \"Threads_connected\";'"
```

**解决**: 增强版Worker已自动处理，会重试3次

### 问题4: 知乎Cookie过期

**症状**: 日志显示"Cookie登录失败或Cookie不存在"

**解决**:
1. 访问: http://39.105.12.124:8080/account/manage
2. 重新登录知乎账号
3. 系统自动保存新Cookie

## 重启服务

### 重启Gunicorn

```bash
ssh u_topn@39.105.12.124 "
pkill -f 'gunicorn.*app_factory'
cd /home/u_topn/TOP_N
nohup python3 -m gunicorn -w 4 -b 0.0.0.0:8080 \
    --timeout 120 \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    backend.app_factory:app >> logs/gunicorn.log 2>&1 &
echo 'Gunicorn restarted'
"
```

### 重启Worker

```bash
ssh u_topn@39.105.12.124 "bash /home/u_topn/TOP_N/backend/start_workers.sh"
```

### 重启所有服务

```bash
ssh u_topn@39.105.12.124 "
cd /home/u_topn/TOP_N

# 停止所有
pkill -f 'gunicorn.*app_factory'
pkill -f 'rq worker'
sleep 2

# 启动Gunicorn
nohup python3 -m gunicorn -w 4 -b 0.0.0.0:8080 \
    --timeout 120 \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    backend.app_factory:app >> logs/gunicorn.log 2>&1 &

# 启动Worker
bash backend/start_workers.sh

echo 'All services restarted'
"
```

## 性能监控

### 监控任务处理速度

```bash
ssh u_topn@39.105.12.124 "cd /home/u_topn/TOP_N/backend && python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')
from models import PublishTask, get_db_session
from datetime import datetime, timedelta

db = get_db_session()

# 最近1小时的任务
one_hour_ago = datetime.now() - timedelta(hours=1)
recent = db.query(PublishTask).filter(
    PublishTask.created_at >= one_hour_ago
).all()

success_count = sum(1 for t in recent if t.status == 'success')
failed_count = sum(1 for t in recent if t.status == 'failed')
total = len(recent)

if total > 0:
    success_rate = (success_count / total) * 100
    print(f'最近1小时任务统计:')
    print(f'  总数: {total}')
    print(f'  成功: {success_count}')
    print(f'  失败: {failed_count}')
    print(f'  成功率: {success_rate:.1f}%')
else:
    print('最近1小时无任务')

db.close()
PYEOF
"
```

### 监控Worker负载

```bash
ssh u_topn@39.105.12.124 "
ps aux | grep 'rq worker' | grep -v grep | awk '{print \$2, \$3, \$4, \$11, \$12}'
"
```

## 备份和恢复

### 备份数据库

```bash
ssh u_topn@39.105.12.124 "
mysqldump -u topn_user -p topn_platform > /tmp/topn_backup_\$(date +%Y%m%d_%H%M%S).sql
"
```

### 回滚到原版Worker

```bash
ssh u_topn@39.105.12.124 "
cd /home/u_topn/TOP_N/backend/services
mv publish_worker.py publish_worker_enhanced.py
mv publish_worker.py.old publish_worker.py
bash ../start_workers.sh
"
```

## 配置修改

### 修改日志级别

```bash
# 改为INFO
ssh u_topn@39.105.12.124 "
sed -i \"123s/LOG_LEVEL = 'DEBUG'/LOG_LEVEL = 'INFO'/\" /home/u_topn/TOP_N/backend/config.py
"

# 重启服务
ssh u_topn@39.105.12.124 "bash /home/u_topn/TOP_N/backend/start_workers.sh"
```

### 修改Worker数量

编辑 `/home/u_topn/TOP_N/backend/start_workers.sh`:
```bash
for i in {1..4}; do  # 改为 {1..8} 启动8个Worker
```

## 测试脚本

### 测试完整流程

```bash
# 1. 清空所有任务（谨慎！）
ssh u_topn@39.105.12.124 "cd /home/u_topn/TOP_N/backend && python3 -c '
import sys; sys.path.insert(0, \".\")
from models import PublishTask, get_db_session
db = get_db_session()
db.query(PublishTask).delete()
db.commit()
print(\"所有任务已清空\")
db.close()
'"

# 2. 访问系统创建测试文章
echo "访问: http://39.105.12.124:8080"

# 3. 发布文章

# 4. 实时监控
ssh u_topn@39.105.12.124 "tail -f /home/u_topn/TOP_N/logs/worker-1.log"
```

## 关键文件位置

```
/home/u_topn/TOP_N/
├── backend/
│   ├── app_factory.py           # 应用入口
│   ├── config.py                # 配置文件
│   ├── models.py                # 数据模型
│   ├── services/
│   │   ├── publish_worker.py    # Worker（增强版）
│   │   ├── publish_worker.py.old # 原版备份
│   │   ├── task_queue_manager.py # 队列管理器
│   │   └── user_rate_limiter.py  # 限流器
│   ├── zhihu_auto_post_enhanced.py # 知乎发布器
│   └── start_workers.sh         # Worker启动脚本
└── logs/
    ├── worker-1.log             # Worker日志
    ├── error.log                # 应用错误日志
    └── access.log               # 访问日志
```

## 联系支持

如遇问题无法解决：
1. 保存完整的错误日志
2. 记录复现步骤
3. 提供系统状态信息

---

**最后更新**: 2025-12-10 23:16
**系统版本**: Enhanced v2.0
