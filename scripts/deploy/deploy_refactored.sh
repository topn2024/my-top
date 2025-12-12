#!/bin/bash
# 部署重构后的代码到服务器

SERVER_USER="u_topn"
SERVER_HOST="39.105.12.124"
SERVER_PASSWORD="@WSX2wsx"
REMOTE_BASE="/home/u_topn/TOP_N"
LOCAL_BASE="D:/work/code/TOP_N"

echo "=========================================="
echo "TOP_N Refactored Code Deployment"
echo "=========================================="

# 1. 备份当前代码
echo ""
echo "Step 1: Backup current code..."
sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST \
  "cd $REMOTE_BASE && cp -r backend backend_backup_\$(date +%Y%m%d_%H%M%S)"
echo "Backup completed!"

# 2. 上传config.py
echo ""
echo "Step 2: Upload config.py..."
sshpass -p "$SERVER_PASSWORD" scp -o StrictHostKeyChecking=no \
  "$LOCAL_BASE/backend/config.py" \
  $SERVER_USER@$SERVER_HOST:$REMOTE_BASE/backend/
echo "config.py uploaded!"

# 3. 上传app_factory.py
echo ""
echo "Step 3: Upload app_factory.py..."
sshpass -p "$SERVER_PASSWORD" scp -o StrictHostKeyChecking=no \
  "$LOCAL_BASE/backend/app_factory.py" \
  $SERVER_USER@$SERVER_HOST:$REMOTE_BASE/backend/
echo "app_factory.py uploaded!"

# 4. 上传services目录
echo ""
echo "Step 4: Upload services directory..."
sshpass -p "$SERVER_PASSWORD" scp -o StrictHostKeyChecking=no -r \
  "$LOCAL_BASE/backend/services" \
  $SERVER_USER@$SERVER_HOST:$REMOTE_BASE/backend/
echo "services uploaded!"

# 5. 上传blueprints目录
echo ""
echo "Step 5: Upload blueprints directory..."
sshpass -p "$SERVER_PASSWORD" scp -o StrictHostKeyChecking=no -r \
  "$LOCAL_BASE/backend/blueprints" \
  $SERVER_USER@$SERVER_HOST:$REMOTE_BASE/backend/
echo "blueprints uploaded!"

# 6. 验证文件
echo ""
echo "Step 6: Verify files..."
sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST \
  "ls -lh $REMOTE_BASE/backend/app_factory.py && ls -lh $REMOTE_BASE/backend/services/ && ls -lh $REMOTE_BASE/backend/blueprints/"
echo "Files verified!"

# 7. 停止旧服务
echo ""
echo "Step 7: Stop old service..."
sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST \
  "pkill -9 -f 'gunicorn.*app' || echo 'No process to kill'"
echo "Waiting 3 seconds..."
sleep 3
echo "Old service stopped!"

# 8. 启动新服务
echo ""
echo "Step 8: Start new service (app_factory)..."
sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST \
  "cd $REMOTE_BASE/backend && nohup python3.14 -m gunicorn --config $REMOTE_BASE/gunicorn_config.py app_factory:app > $REMOTE_BASE/logs/gunicorn.log 2>&1 &"
echo "Waiting 5 seconds for service to start..."
sleep 5
echo "New service started!"

# 9. 验证服务
echo ""
echo "Step 9: Verify service..."
sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST \
  "ps aux | grep 'app_factory' | grep -v grep"
sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST \
  "netstat -tuln | grep 8080"
echo "Service verified!"

# 10. 测试API
echo ""
echo "Step 10: Test API..."
sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST \
  "curl -s http://localhost:8080/ | head -10"
echo "API tested!"

# 11. 查看日志
echo ""
echo "Step 11: Check logs..."
sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST \
  "tail -20 $REMOTE_BASE/logs/gunicorn_error.log"

echo ""
echo "=========================================="
echo "DEPLOYMENT SUCCESSFUL!"
echo "=========================================="
echo ""
echo "Service URL: http://39.105.12.124:8080"
echo "Architecture: app_factory + services + blueprints"
echo ""
echo "To rollback:"
echo "  ssh $SERVER_USER@$SERVER_HOST"
echo "  pkill -9 -f gunicorn"
echo "  cd $REMOTE_BASE/backend"
echo "  nohup python3.14 -m gunicorn --config $REMOTE_BASE/gunicorn_config.py app_with_upload:app > $REMOTE_BASE/logs/gunicorn.log 2>&1 &"
