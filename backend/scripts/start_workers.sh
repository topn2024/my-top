#!/bin/bash
# RQ Workers启动脚本

echo "=== 启动RQ Workers ==="

# 切换到项目目录
cd /home/u_topn/TOP_N

# 检查Redis
redis-cli ping > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Redis未运行,请先启动Redis"
    exit 1
fi

echo "✅ Redis运行正常"

# 停止现有worker
echo "停止现有worker..."
pkill -f "rq worker" 2>/dev/null
sleep 2

# 启动4个worker
echo "启动4个RQ worker..."
for i in {1..4}; do
    # Worker日志输出到worker-$i.log，同时追加到all.log
    (
        cd backend
        rq worker \
            default user:1 user:2 user:3 user:4 user:5 \
            --url redis://localhost:6379/0 \
            --name worker-$i \
            --with-scheduler \
            2>&1 | while IFS= read -r line; do
                echo "$line" >> ../logs/worker-$i.log
                echo "[Worker-$i] $line" >> ../logs/all.log
            done
    ) &

    echo "  Worker-$i 已启动 (PID: $!)"
done

sleep 2

# 检查worker状态
echo ""
echo "=== Worker状态 ==="
ps aux | grep "rq worker" | grep -v grep | awk '{print $2, $11, $12, $13, $14}'

# 显示队列信息
echo ""
echo "=== 队列信息 ==="
python3 << PYEOF
import redis
r = redis.Redis(host='localhost', port=6379, db=0)
keys = r.keys('queue:*')
if keys:
    for key in keys:
        qname = key.decode()
        qlen = r.llen(key)
        print(f"  {qname}: {qlen} tasks")
else:
    print("  没有队列")
PYEOF

echo ""
echo "✅ Workers启动完成!"
echo "查看日志: tail -f logs/worker-1.log"
