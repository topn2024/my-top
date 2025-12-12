# TOP_N 多用户并发发布系统 - 用户使用指南

## 📚 目录

1. [系统概述](#系统概述)
2. [快速开始](#快速开始)
3. [API接口文档](#api接口文档)
4. [前端集成](#前端集成)
5. [系统监控](#系统监控)
6. [故障排查](#故障排查)
7. [最佳实践](#最佳实践)

---

## 系统概述

### 功能特性

✅ **多用户并发**: 支持10个用户同时使用系统
✅ **任务隔离**: 每个用户拥有独立的任务队列
✅ **批量发布**: 支持一次提交多篇文章
✅ **实时监控**: 查看任务进度和状态
✅ **自动重试**: 失败任务可自动或手动重试
✅ **限流保护**: 防止单用户过度使用资源

### 系统架构

```
用户浏览器
    ↓
Flask Web服务 (8080端口)
    ↓
Redis任务队列
    ↓
RQ Worker进程 (4个)
    ↓
WebDriver池 → 知乎/其他平台
```

### 限流规则

- **并发限制**: 每个用户最多10个同时执行的任务
- **速率限制**: 每个用户每分钟最多20个新任务
- 超过限制会返回错误,请等待当前任务完成

---

## 快速开始

### 1. 创建第一个任务

**方法1: 使用Python**

```python
# 在服务器上执行
cd /home/u_topn/TOP_N
python3 test_task_api.py
```

**方法2: 使用curl**

```bash
# 先登录
curl -c cookies.txt -X POST \
  -H 'Content-Type: application/json' \
  -d '{"username":"your_username","password":"your_password"}' \
  http://39.105.12.124:8080/auth/login

# 创建任务
curl -b cookies.txt -X POST \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "我的第一篇文章",
    "content": "这是文章内容",
    "platform": "zhihu"
  }' \
  http://39.105.12.124:8080/api/tasks/create
```

**返回示例**:
```json
{
  "success": true,
  "task_id": "6601dc4b-8c86-469a-bfc9-c0df613b049e",
  "status": "queued",
  "message": "任务已创建并入队"
}
```

### 2. 查询任务状态

```bash
curl -b cookies.txt \
  http://39.105.12.124:8080/api/tasks/6601dc4b-8c86-469a-bfc9-c0df613b049e
```

**返回示例**:
```json
{
  "success": true,
  "task": {
    "task_id": "6601dc4b-8c86-469a-bfc9-c0df613b049e",
    "status": "running",
    "progress": 50,
    "article_title": "我的第一篇文章",
    "platform": "zhihu",
    "created_at": "2025-12-10T00:57:07",
    "result_url": null,
    "error_message": null
  }
}
```

### 3. 获取任务列表

```bash
curl -b cookies.txt \
  "http://39.105.12.124:8080/api/tasks/list?limit=10&status=success"
```

---

## API接口文档

### 基础URL
```
http://39.105.12.124:8080/api/tasks
```

### 1. POST /create - 创建单个任务

**请求体**:
```json
{
  "title": "文章标题",
  "content": "文章内容",
  "platform": "zhihu",   // 可选,默认zhihu
  "article_id": 123      // 可选
}
```

**响应**:
```json
{
  "success": true,
  "task_id": "uuid",
  "status": "queued",
  "message": "任务已创建并入队"
}
```

**错误响应**:
```json
{
  "success": false,
  "error": "超过限流限制",
  "message": "当前并发任务: 10/10, 最近1分钟任务数: 20/20"
}
```

### 2. POST /create_batch - 批量创建任务

**请求体**:
```json
{
  "articles": [
    {
      "title": "文章1",
      "content": "内容1",
      "article_id": 1
    },
    {
      "title": "文章2",
      "content": "内容2"
    }
  ],
  "platform": "zhihu"
}
```

**响应**:
```json
{
  "success": true,
  "total": 2,
  "success_count": 2,
  "failed_count": 0,
  "results": [...]
}
```

### 3. GET /<task_id> - 查询任务状态

**响应**:
```json
{
  "success": true,
  "task": {
    "id": 1,
    "task_id": "uuid",
    "user_id": 1,
    "article_title": "标题",
    "platform": "zhihu",
    "status": "running",      // pending/queued/running/success/failed/cancelled
    "progress": 50,           // 0-100
    "result_url": null,
    "error_message": null,
    "created_at": "2025-12-10T00:00:00",
    "started_at": "2025-12-10T00:00:05",
    "completed_at": null
  }
}
```

### 4. GET /list - 获取任务列表

**查询参数**:
- `status`: 状态过滤 (pending/queued/running/success/failed/cancelled)
- `limit`: 返回数量,默认20,最大100
- `offset`: 偏移量,默认0

**响应**:
```json
{
  "success": true,
  "total": 100,
  "tasks": [...],
  "stats": {
    "pending": 10,
    "queued": 5,
    "running": 3,
    "success": 80,
    "failed": 2
  }
}
```

### 5. POST /<task_id>/cancel - 取消任务

只能取消 `pending` 或 `queued` 状态的任务

**响应**:
```json
{
  "success": true,
  "message": "任务已取消"
}
```

### 6. POST /<task_id>/retry - 重试任务

只能重试 `failed` 状态的任务,且未超过最大重试次数(3次)

**响应**:
```json
{
  "success": true,
  "message": "任务已重新入队(第1次重试)"
}
```

### 7. GET /stats - 获取限流统计

**响应**:
```json
{
  "success": true,
  "concurrent_tasks": 3,
  "max_concurrent_tasks": 10,
  "tasks_in_last_minute": 5,
  "max_tasks_per_minute": 20
}
```

---

## 前端集成

### JavaScript示例

详细代码请参考 `frontend_integration_example.js`

**基础使用**:

```javascript
// 1. 创建任务
const result = await PublishAPI.createTask(
  "文章标题",
  "文章内容",
  "zhihu"
);

if (result.success) {
  console.log('任务ID:', result.taskId);

  // 2. 监控进度
  await PublishAPI.monitor(result.taskId, (task) => {
    console.log('进度:', task.progress + '%');
    console.log('状态:', task.status);
  });
}
```

**批量发布**:

```javascript
const articles = [
  { title: "文章1", content: "内容1" },
  { title: "文章2", content: "内容2" }
];

const result = await PublishAPI.createBatch(articles, "zhihu");
console.log(`成功: ${result.success_count}/${result.total}`);
```

**使用任务管理器**:

```html
<!DOCTYPE html>
<html>
<head>
    <title>文章发布</title>
    <script src="/static/frontend_integration_example.js"></script>
</head>
<body>
    <div id="tasks-container"></div>

    <script>
        // 发布文章
        PublishAPI.manager.publishArticle(
            "测试文章",
            "这是测试内容"
        );
    </script>
</body>
</html>
```

---

## 系统监控

### 1. 查看Worker状态

```bash
ssh u_topn@39.105.12.124
ps aux | grep "rq worker"
```

**正常输出**:
```
u_topn  320055  python3 /home/u_topn/.local/bin/rq worker user:1
u_topn  320056  python3 /home/u_topn/.local/bin/rq worker user:1
u_topn  320057  python3 /home/u_topn/.local/bin/rq worker user:1
u_topn  320058  python3 /home/u_topn/.local/bin/rq worker user:1
```

### 2. 查看Worker日志

```bash
# 实时查看
tail -f /home/u_topn/TOP_N/logs/worker-1.log

# 查看最近50行
tail -50 /home/u_topn/TOP_N/logs/worker-1.log
```

### 3. 查看Redis队列

```bash
redis-cli

# 查看所有队列
KEYS rq:queue:*

# 查看特定队列长度
LLEN rq:queue:user:1

# 查看队列中的任务
LRANGE rq:queue:user:1 0 -1
```

### 4. 查看数据库统计

```bash
mysql -h localhost -u admin -p'TopN@MySQL2024' topn_platform -e "
SELECT
  status,
  COUNT(*) as count,
  AVG(progress) as avg_progress
FROM publish_tasks
GROUP BY status;
"
```

**输出示例**:
```
+----------+-------+--------------+
| status   | count | avg_progress |
+----------+-------+--------------+
| queued   |     5 |         0.00 |
| running  |     3 |        45.00 |
| success  |    80 |       100.00 |
| failed   |     2 |        30.00 |
+----------+-------+--------------+
```

### 5. 监控脚本

创建监控脚本 `monitor.sh`:

```bash
#!/bin/bash
while true; do
  clear
  echo "=== TOP_N 系统监控 ==="
  echo ""
  echo "【Worker状态】"
  ps aux | grep "rq worker" | grep -v grep | wc -l
  echo ""
  echo "【Redis队列】"
  redis-cli LLEN rq:queue:user:1
  echo ""
  echo "【任务统计】"
  mysql -h localhost -u admin -p'TopN@MySQL2024' topn_platform -e \
    "SELECT status, COUNT(*) FROM publish_tasks GROUP BY status;"

  sleep 5
done
```

---

## 故障排查

### 问题1: Worker未处理任务

**症状**: 任务一直处于 `queued` 状态

**排查步骤**:

1. 检查Worker是否运行
   ```bash
   ps aux | grep "rq worker"
   ```

2. 检查Worker日志
   ```bash
   tail -50 /home/u_topn/TOP_N/logs/worker-1.log
   ```

3. 检查队列是否有任务
   ```bash
   redis-cli LLEN rq:queue:user:1
   ```

4. 重启Workers
   ```bash
   cd /home/u_topn/TOP_N
   ./backend/start_workers.sh
   ```

### 问题2: 任务执行失败

**症状**: 任务状态变为 `failed`

**排查步骤**:

1. 查看错误信息
   ```bash
   mysql -h localhost -u admin -p'TopN@MySQL2024' topn_platform -e \
     "SELECT task_id, error_message FROM publish_tasks WHERE status='failed' ORDER BY id DESC LIMIT 5;"
   ```

2. 查看Worker日志
   ```bash
   tail -100 /home/u_topn/TOP_N/logs/worker-*.log | grep -A 10 "ERROR\|Exception"
   ```

3. 常见错误及解决方案:
   - `无法获取WebDriver`: 检查Chrome和chromedriver是否安装
   - `未登录`: 检查Cookie文件是否存在
   - `超时`: 增加任务超时时间

### 问题3: 超过限流限制

**症状**: API返回"超过限流限制"

**解决方案**:

1. 查看当前限流状态
   ```bash
   curl -b cookies.txt http://localhost:8080/api/tasks/stats
   ```

2. 等待当前任务完成,或取消部分queued任务

3. 如需调整限流参数,编辑 `backend/services/user_rate_limiter.py`:
   ```python
   self.max_concurrent_tasks = 10  # 并发数
   self.max_tasks_per_minute = 20  # 每分钟任务数
   ```

### 问题4: Redis连接失败

**症状**: 任务创建失败,日志显示Redis错误

**排查步骤**:

1. 检查Redis是否运行
   ```bash
   redis-cli ping
   ```

2. 检查Redis配置
   ```bash
   redis-cli CONFIG GET maxmemory
   ```

3. 重启Redis
   ```bash
   sudo systemctl restart redis
   ```

---

## 最佳实践

### 1. 任务创建

✅ **推荐**:
- 批量创建时,每批不超过10个任务
- 设置合理的article_id,方便后续查询
- 标题和内容要完整,避免后续编辑

❌ **不推荐**:
- 短时间内创建大量任务(超过20/分钟)
- 创建后立即取消
- 重复创建相同内容的任务

### 2. 任务监控

✅ **推荐**:
- 使用轮询监控,间隔3-5秒
- 设置合理的超时时间(5-10分钟)
- 对失败任务及时重试

❌ **不推荐**:
- 频繁轮询(< 1秒)
- 无限期等待
- 忽略失败任务

### 3. 系统维护

**每日检查**:
- Worker进程状态
- Redis内存使用
- 失败任务数量

**每周清理**:
```bash
# 清理7天前的已完成任务
mysql -h localhost -u admin -p'TopN@MySQL2024' topn_platform -e \
  "DELETE FROM publish_tasks
   WHERE status IN ('success', 'failed')
   AND completed_at < DATE_SUB(NOW(), INTERVAL 7 DAY);"

# 清理Redis过期数据
redis-cli --scan --pattern "ratelimit:*" | xargs redis-cli del
```

### 4. 性能优化

**调整Worker数量**:

```bash
# 编辑 start_workers.sh
for i in {1..6}; do  # 从4改为6
```

**调整WebDriver池大小**:

```python
# 在 publish_worker.py 中
driver_pool = get_driver_pool(max_drivers=4)  # 从8改为4
```

**调整限流参数**:

```python
# 在 user_rate_limiter.py 中
self.max_concurrent_tasks = 5  # 从10改为5
```

---

## 附录

### A. 任务状态说明

| 状态 | 说明 | 可进行的操作 |
|------|------|--------------|
| pending | 已创建,等待入队 | 取消 |
| queued | 已入队,等待Worker处理 | 取消 |
| running | Worker正在执行 | 无 |
| success | 执行成功 | 查看结果 |
| failed | 执行失败 | 重试 |
| cancelled | 已取消 | 无 |

### B. 错误代码

| 错误信息 | 原因 | 解决方案 |
|----------|------|----------|
| 未登录 | Session过期 | 重新登录 |
| 超过限流限制 | 任务过多 | 等待或取消任务 |
| 任务不存在 | task_id错误 | 检查ID |
| 无权限查看此任务 | 非任务所有者 | 使用正确的用户 |
| 任务入队失败 | Redis异常 | 检查Redis |
| 无法获取WebDriver | Driver池已满 | 等待或增加池大小 |

### C. 常用命令速查

```bash
# 启动Workers
cd /home/u_topn/TOP_N && ./backend/start_workers.sh

# 停止Workers
pkill -f "rq worker"

# 查看日志
tail -f /home/u_topn/TOP_N/logs/worker-1.log

# 测试系统
python3 /home/u_topn/TOP_N/test_task_api.py

# 清空队列
redis-cli FLUSHDB
```

---

## 技术支持

如遇问题,请检查:
1. Worker日志文件
2. Flask错误日志 (`logs/error.log`)
3. Redis状态
4. MySQL连接

文档最后更新: 2025-12-10
