# 多用户并发系统部署包

## 📦 包含文件清单

### 核心组件 (已创建)
1. `backend/services/webdriver_pool.py` - WebDriver连接池 ✅
2. `backend/services/user_rate_limiter.py` - 用户限流器 ✅
3. `backend/services/task_queue_manager.py` - 任务队列管理器 ✅
4. `backend/services/publish_worker.py` - 发布Worker ✅

### 配置文件 (即将创建)
5. `backend/start_workers.sh` - Worker启动脚本
6. `backend/blueprints/task_api.py` - 任务API接口

## 🚀 快速部署步骤

### 步骤1: 上传所有组件
```bash
cd D:/work/code/TOP_N

# 上传Python服务
scp backend/services/publish_worker.py u_topn@39.105.12.124:/home/u_topn/TOP_N/backend/services/

# 上传启动脚本
scp backend/start_workers.sh u_topn@39.105.12.124:/home/u_topn/TOP_N/backend/
ssh u_topn@39.105.12.124 "chmod +x /home/u_topn/TOP_N/backend/start_workers.sh"
```

### 步骤2: 启动Worker服务
```bash
ssh u_topn@39.105.12.124
cd /home/u_topn/TOP_N
./backend/start_workers.sh
```

### 步骤3: 集成API到app
在`backend/app_factory.py`中添加:
```python
from blueprints.task_api import task_bp
app.register_blueprint(task_bp, url_prefix='/api/tasks')
```

### 步骤4: 重启Web服务
```bash
./start_service.sh restart
```

## ✅ 验证步骤

### 1. 检查Worker状态
```bash
ps aux | grep "rq worker"
# 应该看到4个worker进程
```

### 2. 检查Redis队列
```bash
redis-cli
> KEYS queue:*
> LLEN queue:user:1
```

### 3. 测试API
```bash
# 创建测试任务
curl -X POST http://localhost:8080/api/tasks/create \
  -H "Content-Type: application/json" \
  -d '{
    "title": "测试文章",
    "content": "这是测试内容",
    "platform": "zhihu"
  }'
```

## 📊 系统监控

### 查看Worker日志
```bash
tail -f logs/worker-1.log
tail -f logs/worker-2.log
```

### 查看任务统计
```bash
# SQL查询
mysql -h localhost -u admin -p'TopN@MySQL2024' topn_platform -e "
SELECT status, COUNT(*) as count 
FROM publish_tasks 
GROUP BY status;
"
```

### 查看限流状态
```bash
redis-cli
> KEYS ratelimit:*
> GET ratelimit:user:1:concurrent
```

## 🔧 故障排查

### Worker无法启动
1. 检查Redis连接: `redis-cli ping`
2. 检查Python路径: `which python3`
3. 检查依赖: `python3 -m pip list | grep rq`

### 任务一直pending
1. 检查Worker运行: `ps aux | grep rq`
2. 检查队列: `redis-cli LLEN queue:user:1`
3. 检查Worker日志: `tail logs/worker-1.log`

### WebDriver错误
1. 检查chromedriver: `ls -l /usr/bin/chromedriver`
2. 测试headless模式: 
```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)
driver.get("https://www.baidu.com")
print(driver.title)
driver.quit()
```

## 📈 性能调优

### 调整Worker数量
编辑`start_workers.sh`:
```bash
# 从4个改为2个或6个
for i in {1..2}; do
```

### 调整WebDriver池大小
在`webdriver_pool.py`中:
```python
get_driver_pool(max_drivers=4)  # 从8改为4
```

### 调整限流参数
在`user_rate_limiter.py`中:
```python
self.max_concurrent_tasks = 5  # 从10改为5
self.max_tasks_per_minute = 10  # 从20改为10
```

## 🎯 下一步计划

- [ ] 前端集成(异步任务UI)
- [ ] 监控面板
- [ ] 邮件通知
- [ ] 任务优先级
- [ ] 更多平台支持

