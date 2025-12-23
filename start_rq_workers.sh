#!/bin/bash
# RQ Worker启动脚本
# 用法: ./start_rq_workers.sh [worker_count]
# 默认启动2个worker

WORKER_COUNT=${1:-2}
PROJECT_DIR="$HOME/TOP_N"
BACKEND_DIR="$PROJECT_DIR/backend"
VENV_DIR="$PROJECT_DIR/venv"
LOG_DIR="/tmp"

echo "=== 启动RQ Workers ==="
echo "项目目录: $PROJECT_DIR"
echo "Worker数量: $WORKER_COUNT"

# 停止现有的Worker
echo "停止现有的RQ Worker..."
pkill -f 'rq worker' 2>/dev/null
sleep 2

# 激活虚拟环境并启动Worker
cd "$BACKEND_DIR" || exit 1
source "$VENV_DIR/bin/activate"

for i in $(seq 1 $WORKER_COUNT); do
    echo "启动 worker-$i..."
    PYTHONPATH=. nohup rq worker default user:1 user:2 user:3 user:4 user:5 \
        --url redis://localhost:6379/0 \
        --name worker-$i \
        --with-scheduler \
        > "$LOG_DIR/rq$i.log" 2>&1 &
    sleep 1
done

echo "等待Worker启动..."
sleep 3

# 检查Worker状态
echo ""
echo "=== Worker状态 ==="
ps aux | grep 'rq worker' | grep -v grep

echo ""
echo "=== 完成 ==="
echo "日志文件: $LOG_DIR/rq*.log"
