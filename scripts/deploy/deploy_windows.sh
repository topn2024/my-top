#!/bin/bash
# Windows 环境下的部署脚本

SERVER="39.105.12.124"
USER="u_topn"
PASSWORD="TopN@2024"
DEPLOY_DIR="/home/u_topn/TOP_N"

echo "=========================================="
echo "  部署 TOP_N 平台到服务器 (修复版本)"
echo "=========================================="
echo ""

echo "【1】上传修复后的文件到服务器..."
echo "----------------------------------------"

# 上传修复后的文件
echo "正在上传 backend/app_with_upload.py..."
scp backend/app_with_upload.py ${USER}@${SERVER}:${DEPLOY_DIR}/backend/

echo "正在上传 requirements.txt..."
scp requirements.txt ${USER}@${SERVER}:${DEPLOY_DIR}/

echo "✅ 文件上传完成"
echo ""

echo "【2】安装/更新依赖..."
echo "----------------------------------------"
ssh ${USER}@${SERVER} << 'ENDSSH'
cd /home/u_topn/TOP_N
source venv/bin/activate
pip install -r requirements.txt --upgrade
echo "✅ 依赖安装完成"
ENDSSH

echo ""
echo "【3】重启服务..."
echo "----------------------------------------"
ssh ${USER}@${SERVER} "sudo systemctl restart topn"
sleep 3
echo "✅ 服务已重启"
echo ""

echo "【4】检查服务状态..."
echo "----------------------------------------"
ssh ${USER}@${SERVER} "sudo systemctl status topn --no-pager | head -20"
echo ""

echo "【5】查看最新日志（检查是否有错误）..."
echo "----------------------------------------"
ssh ${USER}@${SERVER} "sudo journalctl -u topn -n 30 --no-pager"
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
echo ""
