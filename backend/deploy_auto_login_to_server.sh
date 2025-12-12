#!/bin/bash
# 部署知乎自动登录功能到服务器 39.105.12.124

echo "=========================================="
echo " 部署知乎自动登录功能到生产服务器"
echo "=========================================="
echo ""

# 服务器配置
SERVER_IP="39.105.12.124"
SERVER_USER="lihanya"
SERVER_PATH="/root/TOP_N/backend"
LOCAL_PATH="/d/work/code/TOP_N/backend"

echo "配置信息："
echo "  服务器: ${SERVER_USER}@${SERVER_IP}"
echo "  远程路径: ${SERVER_PATH}"
echo "  本地路径: ${LOCAL_PATH}"
echo ""

# 步骤1: 本地验证
echo "=========================================="
echo "步骤 1/5: 本地文件验证"
echo "=========================================="

cd "${LOCAL_PATH}" || exit 1

# 运行本地验证
./deploy_auto_login.sh

if [ $? -ne 0 ]; then
    echo "❌ 本地验证失败，请检查文件"
    exit 1
fi

echo ""
echo "=========================================="
echo "步骤 2/5: 上传文件到服务器"
echo "=========================================="

FILES_TO_UPLOAD=(
    "zhihu_auto_post_enhanced.py"
    "app_with_upload.py"
    "deploy_auto_login.sh"
)

for file in "${FILES_TO_UPLOAD[@]}"; do
    echo "上传: $file"
    sshpass -p '@WSX2wsx' scp -o StrictHostKeyChecking=no \
        "${LOCAL_PATH}/${file}" \
        "${SERVER_USER}@${SERVER_IP}:${SERVER_PATH}/${file}"

    if [ $? -eq 0 ]; then
        echo "  ✓ ${file} 上传成功"
    else
        echo "  ✗ ${file} 上传失败"
        exit 1
    fi
done

echo ""
echo "=========================================="
echo "步骤 3/5: 服务器端文件验证"
echo "=========================================="

sshpass -p '@WSX2wsx' ssh -o StrictHostKeyChecking=no ${SERVER_USER}@${SERVER_IP} << 'ENDSSH'
cd /root/TOP_N/backend

echo "检查文件是否存在："
for file in zhihu_auto_post_enhanced.py app_with_upload.py login_tester.py; do
    if [ -f "$file" ]; then
        echo "  ✓ $file 存在"
        ls -lh "$file" | awk '{print "    大小: " $5 ", 修改时间: " $6 " " $7 " " $8}'
    else
        echo "  ✗ $file 不存在"
        exit 1
    fi
done

echo ""
echo "验证代码集成："
if grep -q "from zhihu_auto_post_enhanced import" app_with_upload.py; then
    echo "  ✓ 已导入增强版模块"
else
    echo "  ✗ 未导入增强版模块"
    exit 1
fi

if grep -q "password=password," app_with_upload.py; then
    echo "  ✓ 已添加password参数"
else
    echo "  ✗ 未添加password参数"
    exit 1
fi
ENDSSH

if [ $? -ne 0 ]; then
    echo "❌ 服务器端验证失败"
    exit 1
fi

echo ""
echo "=========================================="
echo "步骤 4/5: 重启服务"
echo "=========================================="

sshpass -p '@WSX2wsx' ssh -o StrictHostKeyChecking=no ${SERVER_USER}@${SERVER_IP} << 'ENDSSH'
cd /root/TOP_N/backend

# 查找并停止旧进程
echo "查找Flask进程..."
FLASK_PID=$(ps aux | grep 'app_with_upload.py' | grep -v grep | awk '{print $2}')

if [ -n "$FLASK_PID" ]; then
    echo "  找到进程 PID: $FLASK_PID"
    echo "  停止旧进程..."
    kill $FLASK_PID
    sleep 2

    # 确认进程已停止
    if ps -p $FLASK_PID > /dev/null 2>&1; then
        echo "  进程未停止，强制终止..."
        kill -9 $FLASK_PID
        sleep 1
    fi
    echo "  ✓ 旧进程已停止"
else
    echo "  未找到运行中的Flask进程"
fi

# 启动新进程
echo ""
echo "启动新服务..."
cd /root/TOP_N/backend

# 创建日志目录
mkdir -p logs

# 启动服务
nohup python3 app_with_upload.py > logs/app.log 2>&1 &
NEW_PID=$!

sleep 3

# 验证服务启动
if ps -p $NEW_PID > /dev/null 2>&1; then
    echo "  ✓ 服务已启动，PID: $NEW_PID"
else
    echo "  ✗ 服务启动失败"
    echo "  查看错误日志："
    tail -20 logs/app.log
    exit 1
fi
ENDSSH

if [ $? -ne 0 ]; then
    echo "❌ 服务重启失败"
    exit 1
fi

echo ""
echo "=========================================="
echo "步骤 5/5: 服务状态验证"
echo "=========================================="

sleep 2

sshpass -p '@WSX2wsx' ssh -o StrictHostKeyChecking=no ${SERVER_USER}@${SERVER_IP} << 'ENDSSH'
# 检查进程
echo "进程状态："
FLASK_PID=$(ps aux | grep 'app_with_upload.py' | grep -v grep | awk '{print $2}')
if [ -n "$FLASK_PID" ]; then
    echo "  ✓ Flask进程运行中，PID: $FLASK_PID"
    ps aux | grep 'app_with_upload.py' | grep -v grep
else
    echo "  ✗ Flask进程未运行"
    exit 1
fi

echo ""
echo "端口监听状态："
if netstat -tuln | grep ':3001' > /dev/null 2>&1; then
    echo "  ✓ 端口3001正在监听"
    netstat -tuln | grep ':3001'
else
    echo "  ⚠ 端口3001未监听（可能还在启动中）"
fi

echo ""
echo "最新日志（最后10行）："
tail -10 /root/TOP_N/backend/logs/app.log
ENDSSH

if [ $? -ne 0 ]; then
    echo "❌ 服务验证失败"
    exit 1
fi

echo ""
echo "=========================================="
echo "           🎉 部署成功完成！"
echo "=========================================="
echo ""
echo "✅ 已部署的功能："
echo "  1. Cookie优先登录"
echo "  2. 自动密码登录fallback"
echo "  3. Cookie自动保存"
echo ""
echo "📝 后续步骤："
echo "  1. 在Web界面配置知乎测试账号"
echo "  2. 测试发布功能"
echo "  3. 监控日志："
echo "     ssh ${SERVER_USER}@${SERVER_IP}"
echo "     tail -f /root/TOP_N/backend/logs/app.log"
echo ""
echo "🔗 访问地址："
echo "  http://${SERVER_IP}:3001"
echo ""
