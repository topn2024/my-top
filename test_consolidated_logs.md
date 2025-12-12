# 集中日志测试指南

## 快速测试步骤

### 1. 查看当前系统状态

```bash
ssh u_topn@39.105.12.124 "
echo '=== Worker状态 ==='
ps aux | grep 'rq worker' | grep -v grep | wc -l
echo '个Worker正在运行'

echo ''
echo '=== 任务队列 ==='
cd /home/u_topn/TOP_N/backend && python3 -c '
import sys; sys.path.insert(0, \".\")
from models import PublishTask, get_db_session
db = get_db_session()
for status in [\"queued\", \"running\"]:
    count = db.query(PublishTask).filter(PublishTask.status == status).count()
    print(f\"{status}: {count}\")
db.close()
'
"
```

### 2. 准备监控日志

**开启实时日志监控**（在另一个终端窗口）：
```bash
ssh u_topn@39.105.12.124 "tail -f /home/u_topn/TOP_N/logs/worker-1.log"
```

### 3. 创建测试任务

访问系统创建测试文章：
```
http://39.105.12.124:8080
```

操作步骤：
1. 点击"创建文章"
2. 输入标题：`测试集中日志 - $(date +%H%M%S)`
3. 输入内容：任意测试内容（建议500字以上）
4. 点击"发布到知乎"

### 4. 观察日志输出

在日志监控窗口，你应该看到：

#### 开始标记
```
================================================================================
任务执行日志 - TaskID: xxx-xxx-xxx
================================================================================
[HH:MM:SS.mmm] [  0.00s] [INFO ] ============================================================
[HH:MM:SS.mmm] [  0.00s] [INFO ] Worker开始执行任务
[HH:MM:SS.mmm] [  0.00s] [INFO ] ============================================================
```

#### 五个阶段
```
[HH:MM:SS.mmm] [  X.XXs] [INFO ] 【步骤1/5】获取任务信息
...
[HH:MM:SS.mmm] [  X.XXs] [INFO ] 【步骤2/5】更新任务状态
...
[HH:MM:SS.mmm] [  X.XXs] [INFO ] 【步骤3/5】获取平台账号
...
[HH:MM:SS.mmm] [  X.XXs] [INFO ] 【步骤4/5】执行发布
...
[HH:MM:SS.mmm] [  X.XXs] [INFO ] 【步骤5/5】更新最终结果
```

#### 结束标记
```
[HH:MM:SS.mmm] [  X.XXs] [INFO ] ✓✓✓ 任务执行成功！
或
[HH:MM:SS.mmm] [  X.XXs] [ERROR] ✗✗✗ 任务执行失败

[HH:MM:SS.mmm] [  X.XXs] [INFO ] 释放限流令牌
[HH:MM:SS.mmm] [  X.XXs] [INFO ] ✓ 限流令牌已释放
================================================================================
总耗时: X.XX秒
================================================================================
```

## 预期结果

### 成功场景（Cookie有效且账号配置正确）

完整日志应包含：
- ✅ 清晰的开始/结束分隔符
- ✅ 5个步骤按顺序执行
- ✅ 每步都有时间戳和耗时
- ✅ "✓ 知乎发布成功"
- ✅ 文章URL显示
- ✅ "✓✓✓ 任务执行成功！"
- ✅ 总耗时显示

### 失败场景（Cookie过期）

完整日志应包含：
- ✅ 前3个步骤正常
- ✅ 步骤4显示"✗ 知乎发布失败: Cookie登录失败"
- ✅ "✗✗✗ 任务执行失败"
- ✅ 明确的错误原因
- ✅ 状态更新为failed
- ✅ 总耗时显示

### MySQL重试场景（如果发生）

日志中应看到：
- ✅ "数据库连接失败，X秒后重试 (尝试 X/3)"
- ✅ 自动重试
- ✅ 最终成功或失败

## 验证清单

### 日志格式检查

```bash
# 检查是否有完整的日志块
ssh u_topn@39.105.12.124 "
grep -c '================================================================================\|任务执行日志' /home/u_topn/TOP_N/logs/worker-1.log
"
```

应该看到成对的分隔符（每个任务2对）

### 检查5个步骤

```bash
# 确认所有步骤都有
ssh u_topn@39.105.12.124 "
grep '【步骤' /home/u_topn/TOP_N/logs/worker-1.log | tail -5
"
```

应该看到：步骤1/5、步骤2/5、步骤3/5、步骤4/5、步骤5/5

### 检查时间格式

```bash
# 查看时间戳格式
ssh u_topn@39.105.12.124 "
grep '\[.*\] \[.*s\]' /home/u_topn/TOP_N/logs/worker-1.log | tail -3
"
```

应该看到类似：`[23:45:01.234] [  8.76s]`

### 检查成功/失败标记

```bash
# 统计成功任务
ssh u_topn@39.105.12.124 "
grep -c '✓✓✓ 任务执行成功' /home/u_topn/TOP_N/logs/worker-*.log
"

# 统计失败任务
ssh u_topn@39.105.12.124 "
grep -c '✗✗✗ 任务执行失败' /home/u_topn/TOP_N/logs/worker-*.log
"
```

## 问题排查

### 如果看不到集中日志

**检查Worker版本**：
```bash
ssh u_topn@39.105.12.124 "
head -5 /home/u_topn/TOP_N/backend/services/publish_worker.py | grep -i 'v3\|集中日志'
"
```

应该看到：`V3 - 集中日志版`

**检查Worker是否重启**：
```bash
ssh u_topn@39.105.12.124 "
ps aux | grep 'rq worker' | grep -v grep | awk '{print \$2, \$9}'
"
```

查看启动时间，应该是最近的时间

### 如果日志格式不对

**重新部署**：
```bash
# 1. 停止Worker
ssh u_topn@39.105.12.124 "pkill -f 'rq worker'"

# 2. 清空日志（可选，便于测试）
ssh u_topn@39.105.12.124 "
> /home/u_topn/TOP_N/logs/worker-1.log
> /home/u_topn/TOP_N/logs/worker-2.log
> /home/u_topn/TOP_N/logs/worker-3.log
> /home/u_topn/TOP_N/logs/worker-4.log
"

# 3. 重启Worker
ssh u_topn@39.105.12.124 "bash /home/u_topn/TOP_N/backend/start_workers.sh"
```

### 如果没有任务执行

**检查队列**：
```bash
ssh u_topn@39.105.12.124 "cd /home/u_topn/TOP_N/backend && python3 -c '
import redis
from rq import Queue
r = redis.Redis(host=\"localhost\", port=6379, db=0, decode_responses=False)
q = Queue(\"user:1\", connection=r)
print(f\"user:1队列: {len(q)} 个任务\")
'"
```

## 提取完整任务日志

### 方法1: 通过TaskID提取

```bash
# 替换 YOUR_TASK_ID 为实际的TaskID
ssh u_topn@39.105.12.124 "
awk '/任务执行日志 - TaskID: YOUR_TASK_ID/,/^=.*总耗时/' /home/u_topn/TOP_N/logs/worker-*.log
"
```

### 方法2: 提取最近N个任务

```bash
# 提取最近3个任务的完整日志
ssh u_topn@39.105.12.124 "
grep -A 100 '任务执行日志 - TaskID:' /home/u_topn/TOP_N/logs/worker-*.log | tail -300
"
```

### 方法3: 只看成功的任务

```bash
ssh u_topn@39.105.12.124 "
awk '/任务执行日志/,/总耗时/' /home/u_topn/TOP_N/logs/worker-*.log | grep -B 50 '✓✓✓ 任务执行成功'
"
```

### 方法4: 只看失败的任务

```bash
ssh u_topn@39.105.12.124 "
awk '/任务执行日志/,/总耗时/' /home/u_topn/TOP_N/logs/worker-*.log | grep -B 50 '✗✗✗ 任务执行失败'
"
```

## 性能分析

### 查看各阶段平均耗时

```bash
ssh u_topn@39.105.12.124 "
# 提取所有总耗时
grep '总耗时:' /home/u_topn/TOP_N/logs/worker-*.log | awk '{print \$2}' > /tmp/times.txt

# 计算统计
python3 << 'PYEOF'
import statistics

with open('/tmp/times.txt') as f:
    times = [float(line.strip().replace('秒', '')) for line in f if line.strip()]

if times:
    print(f'任务数: {len(times)}')
    print(f'平均耗时: {statistics.mean(times):.2f}秒')
    print(f'最小耗时: {min(times):.2f}秒')
    print(f'最大耗时: {max(times):.2f}秒')
    if len(times) > 1:
        print(f'标准差: {statistics.stdev(times):.2f}秒')
PYEOF
"
```

## 对比测试

### 测试场景1: 正常发布
- 确保Cookie有效
- 账号密码正确
- 预期：5个步骤全部成功

### 测试场景2: Cookie过期
- Cookie已过期
- 提供了密码
- 预期：自动切换密码登录，成功

### 测试场景3: 无密码
- Cookie已过期
- 未提供密码
- 预期：步骤4失败，任务标记为failed

### 测试场景4: MySQL重连
- 在发布过程中模拟MySQL短暂不可用
- 预期：自动重试3次，成功

## 总结

使用新的集中日志格式，你可以：

✅ **快速定位问题** - 一眼看到失败在哪个步骤
✅ **分析性能** - 每步耗时清晰可见
✅ **复制日志** - 完整的日志块便于分享
✅ **追踪任务** - TaskID明确标识
✅ **理解流程** - 5个步骤逻辑清晰

---

**测试建议**: 先创建1-2个测试任务，观察日志格式是否符合预期，然后再进行批量测试。
