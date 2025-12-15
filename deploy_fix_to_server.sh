#!/bin/bash

# 部署修复到服务器的脚本
# 用于将本地修复的文件同步到服务器

echo "================================"
echo "部署管理控制台修复到服务器"
echo "================================"

# 服务器配置
SERVER_USER="u_topn"
SERVER_HOST="39.105.12.124"
SERVER_PATH="/home/u_topn/TOP_N"

# 要同步的文件
FILES_TO_SYNC=(
    "backend/auth_decorators.py"
    "backend/app_with_upload.py"
    "templates/admin_dashboard.html"
    "static/user_display.js"
)

echo ""
echo "准备同步以下文件到服务器："
for file in "${FILES_TO_SYNC[@]}"; do
    echo "  - $file"
done

echo ""
read -p "是否继续? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "取消部署"
    exit 0
fi

echo ""
echo "开始同步文件..."

# 同步每个文件
for file in "${FILES_TO_SYNC[@]}"; do
    echo "同步: $file"
    scp "$file" "${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/$file"

    if [ $? -eq 0 ]; then
        echo "✓ $file 同步成功"
    else
        echo "✗ $file 同步失败"
        exit 1
    fi
done

echo ""
echo "所有文件同步完成！"
echo ""
echo "现在需要重启服务器上的应用："
echo "1. SSH 登录服务器: ssh ${SERVER_USER}@${SERVER_HOST}"
echo "2. 进入项目目录: cd ${SERVER_PATH}"
echo "3. 重启应用:"
echo "   - 如果使用 Gunicorn: pkill gunicorn && gunicorn -c backend/gunicorn_config.py backend.app:app"
echo "   - 如果使用 systemd: sudo systemctl restart topn"
echo "   - 如果使用 supervisor: supervisorctl restart topn"
echo ""

read -p "是否现在通过SSH重启服务器应用? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "正在重启服务器应用..."

    # 尝试重启（假设使用 Gunicorn）
    ssh "${SERVER_USER}@${SERVER_HOST}" << 'EOF'
cd /home/u_topn/TOP_N
echo "停止现有进程..."
pkill -9 gunicorn
pkill -9 python

echo "等待进程完全停止..."
sleep 2

echo "启动新的应用进程..."
cd backend
nohup gunicorn -c gunicorn_config.py app:app > ../logs/gunicorn.log 2>&1 &

echo "等待应用启动..."
sleep 3

echo "检查进程状态..."
ps aux | grep gunicorn | grep -v grep

echo ""
echo "应用重启完成！"
echo "请访问 http://39.105.12.124:8080/admin 验证"
EOF

    echo ""
    echo "================================"
    echo "部署完成！"
    echo "================================"
    echo ""
    echo "验证步骤："
    echo "1. 访问登录页面: http://39.105.12.124:8080/login"
    echo "2. 使用管理员账号登录: admin / TopN@2024"
    echo "3. 访问管理控制台: http://39.105.12.124:8080/admin"
    echo ""
else
    echo ""
    echo "文件已同步，请手动重启服务器应用"
fi
