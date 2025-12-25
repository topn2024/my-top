# TOP_N 多用户并发发布架构设计

## 📋 需求分析

### 功能需求
- 支持10个用户并发使用系统
- 每个用户可以同时发布10篇文章
- 总并发任务数: 100个文章发布任务
- 用户间数据完全隔离
- 资源充分利用，及时回收

### 非功能需求
- 系统稳定可靠
- 异常情况充分考虑
- 易于维护
- 充分解耦

## 🏗️ 系统架构设计

### 1. 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        Web层 (Flask)                         │
│  - 4 Gunicorn Workers                                        │
│  - 接收发布请求                                               │
│  - 创建任务并入队                                             │
│  - 返回任务ID给前端                                           │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│                   任务队列层 (Redis + RQ)                     │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  用户任务队列 (Per-User Queues)                     │    │
│  │  - queue:user:1  (最多10个任务)                     │    │
│  │  - queue:user:2  (最多10个任务)                     │    │
│  │  - ...                                               │    │
│  │  - queue:user:10 (最多10个任务)                     │    │
│  └─────────────────────────────────────────────────────┘    │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│                    Worker层 (RQ Workers)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Worker 1 │  │ Worker 2 │  │ Worker 3 │  │ Worker 4 │    │
│  │          │  │          │  │          │  │          │    │
│  │ WebDriver│  │ WebDriver│  │ WebDriver│  │ WebDriver│    │
│  │  Pool    │  │  Pool    │  │  Pool    │  │  Pool    │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│                                                              │
│  - 从队列获取任务                                            │
│  - 执行发布操作                                              │
│  - 更新任务状态                                              │
│  - 释放资源                                                  │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│                  资源池层 (WebDriver Pool)                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Selenium WebDriver连接池                           │    │
│  │  - 最大连接数: 8                                    │    │
│  │  - 空闲超时: 300秒                                  │    │
│  │  - 自动回收                                         │    │
│  │  - 健康检查                                         │    │
│  └─────────────────────────────────────────────────────┘    │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│                    数据库层 (MySQL)                          │
│  - publish_tasks (任务表)                                    │
│  - publish_history (历史记录)                                │
│  - users (用户表)                                            │
│  - articles (文章表)                                         │
└─────────────────────────────────────────────────────────────┘
```

## 📊 数据库设计

### PublishTask 表
```sql
CREATE TABLE publish_tasks (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    task_id VARCHAR(100) UNIQUE NOT NULL,  -- RQ任务ID
    user_id INT NOT NULL,
    article_id INT,  -- NULL表示临时发布
    article_title VARCHAR(500),
    article_content TEXT,
    platform VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,  -- pending, running, success, failed, retry
    progress INT DEFAULT 0,  -- 0-100
    result_url VARCHAR(500),
    error_message TEXT,
    retry_count INT DEFAULT 0,
    max_retries INT DEFAULT 3,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_task_id (task_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

## 🔧 核心组件设计

### 1. TaskQueueManager (任务队列管理器)
```python
class TaskQueueManager:
    """任务队列管理器 - 负责任务创建和入队"""

    def __init__(self, redis_conn):
        self.redis = redis_conn
        self.max_tasks_per_user = 10  # 每用户最大并发任务数

    def create_publish_task(self, user_id, article_data, platform):
        """创建发布任务"""
        # 1. 检查用户当前任务数
        # 2. 创建任务记录
        # 3. 入队到用户专属队列
        # 4. 返回任务ID

    def get_user_queue_name(self, user_id):
        """获取用户专属队列名"""
        return f'queue:user:{user_id}'

    def get_user_task_count(self, user_id):
        """获取用户当前任务数"""

    def cancel_task(self, task_id):
        """取消任务"""
```

### 2. PublishWorker (发布工作器)
```python
class PublishWorker:
    """发布工作器 - 负责执行发布任务"""

    def __init__(self, webdriver_pool):
        self.driver_pool = webdriver_pool

    def execute_publish_task(self, task_id):
        """执行发布任务"""
        # 1. 从数据库获取任务详情
        # 2. 更新状态为running
        # 3. 从连接池获取WebDriver
        # 4. 执行发布操作
        # 5. 更新任务状态和结果
        # 6. 释放WebDriver回连接池
        # 7. 异常处理和重试
```

### 3. WebDriverPool (WebDriver连接池)
```python
class WebDriverPool:
    """Selenium WebDriver连接池"""

    def __init__(self, max_drivers=8, idle_timeout=300):
        self.max_drivers = max_drivers
        self.idle_timeout = idle_timeout
        self.available_drivers = queue.Queue()
        self.in_use_drivers = set()
        self.lock = threading.RLock()

    def acquire(self, timeout=30):
        """获取一个WebDriver实例"""
        # 1. 尝试从可用池获取
        # 2. 如果没有且未达上限，创建新的
        # 3. 如果已达上限，等待
        # 4. 超时抛出异常

    def release(self, driver):
        """释放WebDriver回池中"""
        # 1. 清理浏览器状态(清除cookies等)
        # 2. 放回可用池
        # 3. 记录最后使用时间

    def cleanup_idle_drivers(self):
        """清理空闲超时的WebDriver"""

    def close_all(self):
        """关闭所有WebDriver"""
```

### 4. UserRateLimiter (用户限流器)
```python
class UserRateLimiter:
    """用户级别限流器"""

    def __init__(self, redis_conn):
        self.redis = redis_conn

    def check_rate_limit(self, user_id):
        """检查用户是否超过速率限制"""
        # 使用Redis实现滑动窗口限流
        # 每用户每分钟最多创建20个任务
        # 每用户同时最多10个运行中的任务

    def acquire(self, user_id):
        """获取令牌"""

    def release(self, user_id):
        """释放令牌"""
```

## 🔄 任务流程

### 发布任务流程
```
1. 用户点击"发布" → Web API接收请求
   ↓
2. 验证用户身份和权限
   ↓
3. 检查用户任务限制 (UserRateLimiter)
   ├─ 超限 → 返回错误提示
   └─ 未超限 → 继续
   ↓
4. 创建任务记录 (TaskQueueManager)
   - 生成task_id
   - 保存到数据库(status=pending)
   - 创建RQ任务
   ↓
5. 任务入队到用户专属队列
   - queue:user:{user_id}
   ↓
6. 返回task_id给前端
   ↓
7. Worker从队列获取任务
   ↓
8. 执行发布操作 (PublishWorker)
   - 更新status=running
   - 从WebDriver池获取driver
   - 登录知乎
   - 发布文章
   - 获取发布URL
   ↓
9. 更新任务状态
   ├─ 成功 → status=success, 保存URL
   ├─ 失败 → status=failed, 判断是否重试
   │   ├─ retry_count < max_retries → 重新入队
   │   └─ retry_count >= max_retries → 最终失败
   └─ 异常 → 记录错误，释放资源
   ↓
10. 释放WebDriver回池
    ↓
11. 前端轮询或WebSocket获取任务状态
```

## 🛡️ 异常处理机制

### 1. Worker崩溃
- RQ自动重试机制
- 任务超时自动标记为失败
- 定时任务清理zombie任务

### 2. WebDriver异常
- 连接池自动检测dead driver
- 健康检查定期执行
- 异常driver自动重建

### 3. 网络异常
- 重试机制(指数退避)
- 超时控制
- 降级策略

### 4. 资源耗尽
- 连接池满时等待或拒绝
- 优雅降级
- 用户友好的错误提示

### 5. 数据库异常
- 连接池重试
- 事务回滚
- 错误日志记录

## 📈 性能优化策略

### 1. 资源配置(基于1.8GB内存, 2核CPU)
```
- Gunicorn Workers: 4个
- RQ Workers: 4个
- WebDriver Pool: 8个driver (共享)
- Redis: 内存限制200MB
- MySQL: 连接池30个连接
```

### 2. 任务优先级
```python
# 普通发布: 低优先级
# VIP用户: 中优先级
# 紧急发布: 高优先级
```

### 3. 缓存策略
- Redis缓存用户Cookie
- 本地缓存WebDriver状态
- 数据库查询结果缓存

### 4. 批量操作
- 批量查询任务状态
- 批量更新数据库
- 减少数据库往返次数

## 🔌 API接口设计

### 1. 创建发布任务
```
POST /api/publish/create_batch
{
    "articles": [
        {"title": "...", "content": "...", "article_id": 1},
        {"title": "...", "content": "...", "article_id": 2}
    ],
    "platform": "zhihu"
}

Response:
{
    "success": true,
    "task_ids": ["task-uuid-1", "task-uuid-2"],
    "message": "已创建2个发布任务"
}
```

### 2. 查询任务状态
```
GET /api/publish/tasks/status?task_ids=task-uuid-1,task-uuid-2

Response:
{
    "success": true,
    "tasks": [
        {
            "task_id": "task-uuid-1",
            "status": "running",
            "progress": 60,
            "article_title": "...",
            "created_at": "2024-12-10T00:00:00"
        }
    ]
}
```

### 3. 取消任务
```
POST /api/publish/tasks/cancel
{
    "task_id": "task-uuid-1"
}
```

### 4. 获取用户任务列表
```
GET /api/publish/tasks/list?status=running&page=1&limit=20

Response:
{
    "success": true,
    "tasks": [...],
    "total": 5,
    "page": 1,
    "limit": 20
}
```

## 📱 前端集成

### 1. 任务提交
```javascript
async function submitPublishBatch(articles) {
    const response = await fetch('/api/publish/create_batch', {
        method: 'POST',
        body: JSON.stringify({
            articles: articles,
            platform: 'zhihu'
        })
    });

    const data = await response.json();
    return data.task_ids;
}
```

### 2. 任务状态轮询
```javascript
async function pollTaskStatus(taskIds) {
    const interval = setInterval(async () => {
        const response = await fetch(
            `/api/publish/tasks/status?task_ids=${taskIds.join(',')}`
        );
        const data = await response.json();

        // 更新UI
        updateTaskUI(data.tasks);

        // 所有任务完成，停止轮询
        if (allTasksCompleted(data.tasks)) {
            clearInterval(interval);
        }
    }, 3000);  // 每3秒轮询一次
}
```

## 🔧 部署配置

### 1. 安装依赖
```bash
pip install redis rq
pip install selenium
```

### 2. Redis配置
```bash
# 安装Redis
yum install redis -y

# 启动Redis
systemctl start redis
systemctl enable redis

# 配置内存限制
redis-cli CONFIG SET maxmemory 200mb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### 3. 启动RQ Workers
```bash
# backend/start_workers.sh
#!/bin/bash
cd /home/u_topn/TOP_N

# 启动4个worker
for i in {1..4}; do
    nohup rq worker queue:user:* \
        --url redis://localhost:6379/0 \
        --name worker-$i \
        >> logs/worker-$i.log 2>&1 &
done

echo "Workers started"
```

### 4. 系统服务配置
```ini
# /etc/systemd/system/topn-workers.service
[Unit]
Description=TOP_N RQ Workers
After=network.target redis.service

[Service]
Type=forking
User=u_topn
WorkingDirectory=/home/u_topn/TOP_N
ExecStart=/home/u_topn/TOP_N/backend/start_workers.sh
ExecStop=/usr/bin/pkill -f "rq worker"
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

## 📊 监控指标

### 关键指标
- 任务队列长度 (per user)
- Worker CPU/内存使用率
- WebDriver池使用情况
- 任务成功率
- 平均任务耗时
- 并发用户数

### 监控方案
```python
# backend/services/metrics_service.py
class MetricsService:
    def get_system_metrics(self):
        return {
            'active_users': self.count_active_users(),
            'total_tasks': self.count_total_tasks(),
            'running_tasks': self.count_running_tasks(),
            'driver_pool_usage': self.get_driver_pool_stats(),
            'queue_lengths': self.get_all_queue_lengths(),
            'success_rate': self.calculate_success_rate()
        }
```

## 🧪 测试计划

### 1. 单元测试
- TaskQueueManager
- PublishWorker
- WebDriverPool
- UserRateLimiter

### 2. 集成测试
- 完整发布流程
- 异常恢复
- 并发测试

### 3. 压力测试
```python
# 测试场景: 10用户 x 10文章 = 100并发任务
def stress_test():
    users = create_test_users(10)
    for user in users:
        articles = create_test_articles(10)
        submit_publish_batch(user, articles)

    # 监控系统指标
    monitor_metrics()
```

## 📝 维护指南

### 日常维护
- 检查Worker进程状态
- 清理过期任务记录
- 监控资源使用
- 检查错误日志

### 故障排查
```bash
# 检查RQ队列状态
rq info --url redis://localhost:6379/0

# 检查Worker状态
ps aux | grep "rq worker"

# 查看任务详情
redis-cli LRANGE queue:user:1 0 -1

# 清空失败任务
rq empty --all
```

## 🚀 实施步骤

1. **第一阶段**: 基础设施搭建
   - 安装Redis
   - 创建数据库表
   - 配置RQ

2. **第二阶段**: 核心组件开发
   - TaskQueueManager
   - PublishWorker
   - WebDriverPool

3. **第三阶段**: API开发
   - 任务创建API
   - 状态查询API
   - 取消/重试API

4. **第四阶段**: 前端集成
   - 批量提交界面
   - 任务状态展示
   - 进度条显示

5. **第五阶段**: 测试和优化
   - 单元测试
   - 压力测试
   - 性能优化

6. **第六阶段**: 部署上线
   - 配置生产环境
   - 灰度发布
   - 监控告警

---

**预计开发时间**: 2-3周
**技术栈**: Python, Flask, Redis, RQ, Selenium, MySQL
**资源需求**: 2核CPU, 2GB内存, Redis, MySQL
