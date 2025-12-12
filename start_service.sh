#!/bin/bash
# 启动 TOP_N 服务脚本

# 项目目录
DEPLOY_DIR="/home/u_topn/TOP_N"

# 切换到项目目录
cd $DEPLOY_DIR

# 停止现有服务
pkill -f gunicorn
sleep 2

# 设置 PYTHONPATH
export PYTHONPATH=$DEPLOY_DIR/backend:$DEPLOY_DIR:$PYTHONPATH

# 启动服务
nohup python3 -m gunicorn \
  -w 4 \
  -b 0.0.0.0:8080 \
  --timeout 120 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log \
  'backend.app_factory:app' \
  > logs/startup.log 2>&1 &

echo "服务启动命令已执行"
sleep 3

# 检查服务
ps aux | grep gunicorn | grep -v grep

echo ""
echo "服务已启动!"
echo "访问地址: http://39.105.12.124:8080"
