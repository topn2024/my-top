#!/bin/bash

# TOP_N 部署脚本
# 部署到服务器 39.105.12.124:8080

SERVER="39.105.12.124"
USER="u_topn"
DEPLOY_DIR="/home/u_topn/TOP_N"

echo "=========================================="
echo "  部署 TOP_N 平台到服务器"
echo "=========================================="
echo ""

echo "【1】上传文件到服务器..."
echo "----------------------------------------"

# 创建远程目录
ssh ${USER}@${SERVER} "mkdir -p ${DEPLOY_DIR}"

# 上传项目文件
rsync -avz --exclude='venv' --exclude='__pycache__' --exclude='*.pyc' --exclude='.git' \
    ./ ${USER}@${SERVER}:${DEPLOY_DIR}/ 2>&1 || \
scp -r backend templates static requirements.txt start.sh ${USER}@${SERVER}:${DEPLOY_DIR}/

echo "✅ 文件上传完成"
echo ""

echo "【2】安装依赖..."
echo "----------------------------------------"
ssh ${USER}@${SERVER} "cd ${DEPLOY_DIR} && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"

echo "✅ 依赖安装完成"
echo ""

echo "【3】创建启动服务..."
echo "----------------------------------------"

# 创建systemd服务文件
ssh ${USER}@${SERVER} "cat > /tmp/topn.service << 'EOF'
[Unit]
Description=TOP_N Platform
After=network.target

[Service]
Type=simple
User=u_topn
WorkingDirectory=${DEPLOY_DIR}/backend
Environment=PATH=${DEPLOY_DIR}/venv/bin
ExecStart=${DEPLOY_DIR}/venv/bin/python3 app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
"

# 安装服务
ssh ${USER}@${SERVER} "sudo mv /tmp/topn.service /etc/systemd/system/ && \
    sudo systemctl daemon-reload && \
    sudo systemctl enable topn && \
    sudo systemctl restart topn"

echo "✅ 服务创建完成"
echo ""

echo "【4】配置防火墙..."
echo "----------------------------------------"
ssh ${USER}@${SERVER} "sudo firewall-cmd --permanent --add-port=8080/tcp 2>&1 || \
    sudo iptables -I INPUT -p tcp --dport 8080 -j ACCEPT 2>&1 || \
    echo '防火墙已开放或无需配置'"

echo "✅ 防火墙配置完成"
echo ""

echo "【5】检查服务状态..."
echo "----------------------------------------"
ssh ${USER}@${SERVER} "sudo systemctl status topn --no-pager | head -15"

echo ""
echo "=========================================="
echo "  ✅ 部署完成！"
echo "=========================================="
echo ""
echo "访问地址："
echo "  http://39.105.12.124:8080"
echo ""
echo "管理命令："
echo "  查看状态: ssh ${USER}@${SERVER} 'sudo systemctl status topn'"
echo "  查看日志: ssh ${USER}@${SERVER} 'sudo journalctl -u topn -f'"
echo "  重启服务: ssh ${USER}@${SERVER} 'sudo systemctl restart topn'"
echo "  停止服务: ssh ${USER}@${SERVER} 'sudo systemctl stop topn'"
echo ""
