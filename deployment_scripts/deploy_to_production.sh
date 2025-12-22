#!/bin/bash
# 生产环境部署脚本
# 用途：将app_factory架构部署到生产服务器

set -e  # 遇到错误立即退出

SERVER="u_topn@39.105.12.124"
REMOTE_DIR="/home/u_topn/TOP_N"
LOCAL_BACKEND="D:/code/TOP_N/backend"

echo "========================================="
echo "TOP_N 生产环境部署 - Phase 4"
echo "========================================="
echo ""

# 0. 确认部署
read -p "确认要部署到生产环境? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "部署已取消"
    exit 0
fi

# 1. 在服务器上创建备份
echo "[步骤 1/8] 创建部署前备份..."
ssh ${SERVER} 'bash -s' < backup_before_deploy.sh > /tmp/backup_output.txt
BACKUP_ID=$(grep "备份ID:" /tmp/backup_output.txt | cut -d: -f2 | tr -d ' ')
echo "备份ID: ${BACKUP_ID}"
echo "备份完成"

# 2. 上传修复的文件
echo ""
echo "[步骤 2/8] 上传修复的文件..."

# 2.1 上传blueprints/api.py
echo "  - 上传 blueprints/api.py"
scp "${LOCAL_BACKEND}/blueprints/api.py" ${SERVER}:${REMOTE_DIR}/backend/blueprints/

# 2.2 上传models.py
echo "  - 上传 models.py"
scp "${LOCAL_BACKEND}/models.py" ${SERVER}:${REMOTE_DIR}/backend/

# 2.3 上传config.py
echo "  - 上传 config.py"
scp "${LOCAL_BACKEND}/config.py" ${SERVER}:${REMOTE_DIR}/backend/

# 2.4 上传app_factory.py
echo "  - 上传 app_factory.py"
scp "${LOCAL_BACKEND}/app_factory.py" ${SERVER}:${REMOTE_DIR}/backend/

# 2.5 上传app.py
echo "  - 上传 app.py"
scp "${LOCAL_BACKEND}/app.py" ${SERVER}:${REMOTE_DIR}/backend/

# 2.6 上传.env.example
echo "  - 上传 .env.example"
scp "${LOCAL_BACKEND}/.env.example" ${SERVER}:${REMOTE_DIR}/backend/

echo "文件上传完成"

# 3. 在服务器上创建生产环境.env文件
echo ""
echo "[步骤 3/8] 创建生产环境.env文件..."
ssh ${SERVER} << 'ENDSSH'
cd /home/u_topn/TOP_N/backend

# 只在.env不存在时创建
if [ ! -f .env ]; then
    cat > .env << 'EOF'
# TOP_N 生产环境配置
TOPN_SECRET_KEY=TopN_Secret_Key_2024_Please_Change_In_Production
FLASK_ENV=production

# AI API 密钥
ZHIPU_API_KEY=d6ac02f8c1f6f443cf81f3dae86fb095.7Qe6KOWcVDlDlqDJ
QIANWEN_API_KEY=sk-f0a85d3e56a746509ec435af2446c67a
AI_PROVIDER=zhipu
DEFAULT_AI_MODEL=glm-4-plus

# 数据库配置
DATABASE_URL=sqlite:///topn.db

# 日志配置
LOG_LEVEL=INFO
LOG_DIR=logs

# 服务器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=8080
EOF
    chmod 600 .env
    echo ".env 文件已创建"
else
    echo ".env 文件已存在，跳过"
fi
ENDSSH

# 4. 更新systemd配置
echo ""
echo "[步骤 4/8] 更新systemd配置..."
ssh ${SERVER} << 'ENDSSH'
sudo tee /etc/systemd/system/topn.service > /dev/null << 'EOF'
[Unit]
Description=TOP_N Platform with Gunicorn (app_factory)
After=network.target mysql.service
Wants=mysql.service

[Service]
Type=notify
User=u_topn
Group=u_topn
WorkingDirectory=/home/u_topn/TOP_N/backend
Environment="PATH=/home/u_topn/.local/bin:/usr/local/bin:/usr/bin"
Environment="PYTHONUNBUFFERED=1"
Environment="DISPLAY=:0"
Environment="CHROME_BIN=/usr/bin/google-chrome"
ExecStart=/home/u_topn/.local/bin/gunicorn --config /home/u_topn/TOP_N/gunicorn_config.py app:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
echo "systemd配置已更新 (app_with_upload:app -> app:app)"
ENDSSH

# 5. 重启服务
echo ""
echo "[步骤 5/8] 重启服务..."
ssh ${SERVER} "sudo systemctl restart topn.service"
echo "等待服务启动..."
sleep 10

# 6. 验证服务状态
echo ""
echo "[步骤 6/8] 验证服务状态..."
ssh ${SERVER} << 'ENDSSH'
if sudo systemctl is-active --quiet topn.service; then
    echo "服务运行状态: 正常"
else
    echo "错误: 服务未运行！"
    sudo systemctl status topn.service --no-pager
    exit 1
fi
ENDSSH

# 7. 健康检查
echo ""
echo "[步骤 7/8] 健康检查..."
HEALTH_CHECK=$(ssh ${SERVER} "curl -s http://localhost:8080/api/health")
echo "健康检查响应: ${HEALTH_CHECK}"

if echo "${HEALTH_CHECK}" | grep -q "ok"; then
    echo "健康检查: 通过"
else
    echo "错误: 健康检查失败！"
    echo "开始回滚..."
    bash rollback_deployment.sh ${BACKUP_ID}
    exit 1
fi

# 8. 验证修复的路由
echo ""
echo "[步骤 8/8] 验证修复的路由..."
echo "测试 /api/platforms 路由..."
PLATFORMS_CODE=$(ssh ${SERVER} "curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/api/platforms")
echo "  状态码: ${PLATFORMS_CODE}"

if [ "${PLATFORMS_CODE}" = "401" ] || [ "${PLATFORMS_CODE}" = "200" ]; then
    echo "  路由验证: 通过 (${PLATFORMS_CODE})"
else
    echo "  警告: 路由返回 ${PLATFORMS_CODE}"
fi

echo ""
echo "========================================="
echo "部署完成！"
echo "========================================="
echo ""
echo "部署信息:"
echo "  - 备份ID: ${BACKUP_ID}"
echo "  - 入口点: app:app (从 app_with_upload:app 切换)"
echo "  - 架构: app_factory 蓝图架构"
echo ""
echo "回滚命令 (如需要):"
echo "  bash rollback_deployment.sh ${BACKUP_ID}"
echo ""
echo "建议接下来:"
echo "  1. 监控日志: ssh ${SERVER} 'tail -f /home/u_topn/TOP_N/logs/gunicorn_error.log'"
echo "  2. 测试功能"
echo "  3. 检查错误率"
