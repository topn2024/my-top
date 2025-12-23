#!/bin/bash
# 部署知乎自动登录功能到服务器

echo "=========================================="
echo "    部署知乎自动登录功能到服务器"
echo "=========================================="
echo ""

SERVER_USER="lihanya"
SERVER_IP="39.105.12.124"
SERVER_PATH="/root/TOP_N/backend"

echo "服务器信息："
echo "  地址: ${SERVER_USER}@${SERVER_IP}"
echo "  路径: ${SERVER_PATH}"
echo ""

# 检查本地文件
echo "1. 检查本地文件..."
FILES_TO_DEPLOY=(
    "zhihu_auto_post_enhanced.py"
    "app_with_upload.py"
    "deploy_auto_login.sh"
)

for file in "${FILES_TO_DEPLOY[@]}"; do
    if [ -f "/d/work/code/TOP_N/backend/$file" ]; then
        echo "  ✓ $file 存在"
    else
        echo "  ✗ $file 不存在"
        exit 1
    fi
done

echo ""
echo "2. 上传文件到服务器..."

# 使用scp上传文件
for file in "${FILES_TO_DEPLOY[@]}"; do
    echo "  上传 $file ..."
    scp -o StrictHostKeyChecking=no \
        "/d/work/code/TOP_N/backend/$file" \
        "${SERVER_USER}@${SERVER_IP}:${SERVER_PATH}/$file"

    if [ $? -eq 0 ]; then
        echo "  ✓ $file 上传成功"
    else
        echo "  ✗ $file 上传失败"
        exit 1
    fi
done

echo ""
echo "3. 验证服务器上的文件..."
ssh -o StrictHostKeyChecking=no ${SERVER_USER}@${SERVER_IP} << 'ENDSSH'
cd /root/TOP_N/backend

echo "  检查文件是否存在："
for file in zhihu_auto_post_enhanced.py app_with_upload.py deploy_auto_login.sh; do
    if [ -f "$file" ]; then
        echo "  ✓ $file 存在"
    else
        echo "  ✗ $file 不存在"
    fi
done

echo ""
echo "  运行部署检查脚本："
chmod +x deploy_auto_login.sh
./deploy_auto_login.sh
ENDSSH

echo ""
echo "4. 重启服务..."
ssh -o StrictHostKeyChecking=no ${SERVER_USER}@${SERVER_IP} << 'ENDSSH'
# 查找并重启Flask应用
echo "  查找Flask进程..."
FLASK_PID=$(ps aux | grep 'app_with_upload.py' | grep -v grep | awk '{print $2}')

if [ -n "$FLASK_PID" ]; then
    echo "  找到Flask进程: $FLASK_PID"
    echo "  停止旧进程..."
    kill $FLASK_PID
    sleep 2
    echo "  ✓ 旧进程已停止"
else
    echo "  未找到运行中的Flask进程"
fi

# 启动新进程
echo "  启动新服务..."
cd /root/TOP_N/backend
nohup python3 app_with_upload.py > /root/TOP_N/backend/logs/app.log 2>&1 &
sleep 3

# 验证服务是否启动
NEW_PID=$(ps aux | grep 'app_with_upload.py' | grep -v grep | awk '{print $2}')
if [ -n "$NEW_PID" ]; then
    echo "  ✓ 服务已启动，PID: $NEW_PID"
else
    echo "  ✗ 服务启动失败"
    exit 1
fi

# 检查端口
echo ""
echo "  检查服务端口..."
netstat -tuln | grep 3001 || echo "  ⚠ 端口3001未监听"
ENDSSH

echo ""
echo "=========================================="
echo "           部署完成！"
echo "=========================================="
echo ""
echo "后续步骤："
echo "1. 在Web界面配置知乎测试账号"
echo "2. 测试发布功能"
echo "3. 查看日志: ssh ${SERVER_USER}@${SERVER_IP} 'tail -f /root/TOP_N/backend/logs/app.log'"
echo ""
