#!/bin/bash
# 多用户并发发布系统 - 完整测试脚本

echo "=========================================="
echo "  TOP_N 多用户并发发布系统 - 测试脚本"
echo "=========================================="

# 测试配置
BASE_URL="http://localhost:8080"
TEST_USER="testuser_$(date +%s)"
TEST_EMAIL="test_$(date +%s)@test.com"
TEST_PASSWORD="Test123!"

echo -e "\n【测试配置】"
echo "Base URL: $BASE_URL"
echo "测试用户: $TEST_USER"
echo "测试邮箱: $TEST_EMAIL"

# 清理旧的cookie文件
rm -f /tmp/concurrent_test_cookies.txt

# ==========================================
# 第一部分: 用户认证测试
# ==========================================
echo -e "\n=========================================="
echo "  第一部分: 用户认证测试"
echo "=========================================="

# 1. 注册新用户
echo -e "\n【1】注册测试用户..."
REGISTER_RESPONSE=$(curl -s -c /tmp/concurrent_test_cookies.txt -X POST \
  -H 'Content-Type: application/json' \
  -d "{\"username\":\"$TEST_USER\",\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\",\"invite_code\":\"topn2024\"}" \
  $BASE_URL/auth/register)

echo "$REGISTER_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$REGISTER_RESPONSE"

# 检查注册是否成功
if echo "$REGISTER_RESPONSE" | grep -q "success.*true\|注册成功"; then
  echo "✅ 用户注册成功"
else
  echo "⚠️  注册返回: $REGISTER_RESPONSE"
  echo "尝试使用现有用户 'admin' 进行测试..."
  TEST_USER="admin"
  TEST_PASSWORD="admin123"
fi

sleep 1

# 2. 用户登录
echo -e "\n【2】用户登录..."
LOGIN_RESPONSE=$(curl -s -b /tmp/concurrent_test_cookies.txt -c /tmp/concurrent_test_cookies.txt -X POST \
  -H 'Content-Type: application/json' \
  -d "{\"username\":\"$TEST_USER\",\"password\":\"$TEST_PASSWORD\"}" \
  $BASE_URL/auth/login)

echo "$LOGIN_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$LOGIN_RESPONSE"

if echo "$LOGIN_RESPONSE" | grep -q "success.*true\|登录成功"; then
  echo "✅ 用户登录成功"
else
  echo "❌ 登录失败,无法继续测试"
  exit 1
fi

sleep 1

# ==========================================
# 第二部分: 任务API测试
# ==========================================
echo -e "\n=========================================="
echo "  第二部分: 任务API测试"
echo "=========================================="

# 3. 获取限流统计 (初始状态)
echo -e "\n【3】获取初始限流统计..."
STATS_RESPONSE=$(curl -s -b /tmp/concurrent_test_cookies.txt \
  $BASE_URL/api/tasks/stats)

echo "$STATS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$STATS_RESPONSE"

if echo "$STATS_RESPONSE" | grep -q "success.*true"; then
  echo "✅ 限流统计API正常"
else
  echo "❌ 限流统计API失败"
fi

sleep 1

# 4. 创建单个任务
echo -e "\n【4】创建单个测试任务..."
CREATE_RESPONSE=$(curl -s -b /tmp/concurrent_test_cookies.txt -c /tmp/concurrent_test_cookies.txt -X POST \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "并发系统测试文章",
    "content": "这是一篇测试多用户并发发布系统的文章。系统采用Redis+RQ架构,支持10个用户同时使用,每个用户可以并发发布10篇文章。",
    "platform": "zhihu"
  }' \
  $BASE_URL/api/tasks/create)

echo "$CREATE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$CREATE_RESPONSE"

# 提取task_id
TASK_ID=$(echo "$CREATE_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('task_id', ''))" 2>/dev/null)

if [ -n "$TASK_ID" ] && [ "$TASK_ID" != "None" ] && [ "$TASK_ID" != "" ]; then
  echo "✅ 任务创建成功! Task ID: $TASK_ID"
else
  echo "❌ 任务创建失败"
  echo "响应: $CREATE_RESPONSE"
  TASK_ID=""
fi

sleep 2

# 5. 查询任务状态
if [ -n "$TASK_ID" ]; then
  echo -e "\n【5】查询任务状态..."
  STATUS_RESPONSE=$(curl -s -b /tmp/concurrent_test_cookies.txt \
    $BASE_URL/api/tasks/$TASK_ID)

  echo "$STATUS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$STATUS_RESPONSE"

  # 提取任务状态
  TASK_STATUS=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('task', {}).get('status', ''))" 2>/dev/null)

  if [ -n "$TASK_STATUS" ]; then
    echo "✅ 任务状态: $TASK_STATUS"
  else
    echo "⚠️  无法获取任务状态"
  fi
fi

sleep 2

# 6. 获取任务列表
echo -e "\n【6】获取任务列表..."
LIST_RESPONSE=$(curl -s -b /tmp/concurrent_test_cookies.txt \
  "$BASE_URL/api/tasks/list?limit=10")

echo "$LIST_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$LIST_RESPONSE"

if echo "$LIST_RESPONSE" | grep -q "success.*true"; then
  TASK_COUNT=$(echo "$LIST_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('tasks', [])))" 2>/dev/null)
  echo "✅ 任务列表获取成功,当前有 $TASK_COUNT 个任务"
else
  echo "❌ 获取任务列表失败"
fi

sleep 2

# 7. 批量创建任务测试
echo -e "\n【7】批量创建任务测试 (3个任务)..."
BATCH_RESPONSE=$(curl -s -b /tmp/concurrent_test_cookies.txt -X POST \
  -H 'Content-Type: application/json' \
  -d '{
    "articles": [
      {"title": "批量测试文章1", "content": "这是批量测试的第一篇文章"},
      {"title": "批量测试文章2", "content": "这是批量测试的第二篇文章"},
      {"title": "批量测试文章3", "content": "这是批量测试的第三篇文章"}
    ],
    "platform": "zhihu"
  }' \
  $BASE_URL/api/tasks/create_batch)

echo "$BATCH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$BATCH_RESPONSE"

if echo "$BATCH_RESPONSE" | grep -q "success.*true"; then
  SUCCESS_COUNT=$(echo "$BATCH_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('success_count', 0))" 2>/dev/null)
  echo "✅ 批量创建成功,成功创建 $SUCCESS_COUNT 个任务"
else
  echo "❌ 批量创建任务失败"
fi

sleep 2

# 8. 获取更新后的限流统计
echo -e "\n【8】获取更新后的限流统计..."
STATS_RESPONSE=$(curl -s -b /tmp/concurrent_test_cookies.txt \
  $BASE_URL/api/tasks/stats)

echo "$STATS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$STATS_RESPONSE"

# ==========================================
# 第三部分: Worker执行验证
# ==========================================
echo -e "\n=========================================="
echo "  第三部分: Worker执行验证"
echo "=========================================="

# 9. 检查Worker状态
echo -e "\n【9】检查Worker进程状态..."
WORKER_COUNT=$(ps aux | grep "rq worker" | grep -v grep | wc -l)
echo "当前运行的Worker数量: $WORKER_COUNT"

if [ $WORKER_COUNT -gt 0 ]; then
  echo "✅ Worker进程正常运行"
  ps aux | grep "rq worker" | grep -v grep | head -4
else
  echo "❌ 没有发现运行中的Worker进程"
fi

# 10. 检查Redis队列
echo -e "\n【10】检查Redis队列状态..."
echo "队列列表:"
redis-cli KEYS "queue:*" 2>/dev/null || echo "无法连接Redis"

echo -e "\n队列长度:"
redis-cli KEYS "queue:*" | while read queue; do
  if [ -n "$queue" ]; then
    len=$(redis-cli LLEN "$queue" 2>/dev/null)
    echo "  $queue: $len 个任务"
  fi
done

# 11. 查看Worker日志
echo -e "\n【11】查看Worker最近日志 (最后20行)..."
if [ -f /home/u_topn/TOP_N/logs/worker-1.log ]; then
  tail -20 /home/u_topn/TOP_N/logs/worker-1.log
else
  echo "Worker日志文件不存在"
fi

# ==========================================
# 第四部分: 数据库验证
# ==========================================
echo -e "\n=========================================="
echo "  第四部分: 数据库验证"
echo "=========================================="

# 12. 查询数据库中的任务统计
echo -e "\n【12】数据库任务统计..."
mysql -h localhost -u admin -p'TopN@MySQL2024' topn_platform -e "
SELECT
  status,
  COUNT(*) as count,
  AVG(progress) as avg_progress
FROM publish_tasks
GROUP BY status;" 2>/dev/null || echo "无法连接数据库"

# ==========================================
# 测试总结
# ==========================================
echo -e "\n=========================================="
echo "  测试总结"
echo "=========================================="

echo -e "\n✅ 已完成的测试项:"
echo "  1. 用户注册和登录"
echo "  2. 创建单个任务"
echo "  3. 查询任务状态"
echo "  4. 获取任务列表"
echo "  5. 批量创建任务"
echo "  6. 限流统计查询"
echo "  7. Worker进程检查"
echo "  8. Redis队列检查"
echo "  9. 数据库统计查询"

echo -e "\n📊 系统状态:"
echo "  - Worker进程数: $WORKER_COUNT/4"
echo "  - 测试用户: $TEST_USER"
if [ -n "$TASK_ID" ]; then
  echo "  - 最新任务ID: $TASK_ID"
  echo "  - 最新任务状态: $TASK_STATUS"
fi

echo -e "\n=========================================="
echo "  测试完成!"
echo "=========================================="
