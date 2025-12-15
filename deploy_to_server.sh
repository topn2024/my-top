#!/bin/bash
# 一键部署脚本 - 将修复后的文件上传到服务器

# 服务器配置
SERVER_USER="u_topn"
SERVER_IP="39.105.12.124"
SERVER_PATH="/data/TOP_N"

echo "========================================="
echo "TOP_N Blueprints 架构修复文件部署"
echo "========================================="
echo ""
echo "目标服务器: $SERVER_USER@$SERVER_IP"
echo "部署路径: $SERVER_PATH"
echo ""

# 确认部署
read -p "是否继续部署？(y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "部署已取消"
    exit 1
fi

echo ""
echo "开始上传修复文件..."
echo ""

# 上传 auth_decorators.py
echo "[1/5] 上传 auth_decorators.py..."
scp backend/auth_decorators.py $SERVER_USER@$SERVER_IP:$SERVER_PATH/backend/
if [ $? -eq 0 ]; then
    echo "  ✓ 上传成功"
else
    echo "  ✗ 上传失败"
    exit 1
fi

# 上传 blueprints/auth.py
echo "[2/5] 上传 blueprints/auth.py..."
scp backend/blueprints/auth.py $SERVER_USER@$SERVER_IP:$SERVER_PATH/backend/blueprints/
if [ $? -eq 0 ]; then
    echo "  ✓ 上传成功"
else
    echo "  ✗ 上传失败"
    exit 1
fi

# 上传 ai_service_v2.py
echo "[3/5] 上传 services/ai_service_v2.py..."
scp backend/services/ai_service_v2.py $SERVER_USER@$SERVER_IP:$SERVER_PATH/backend/services/
if [ $? -eq 0 ]; then
    echo "  ✓ 上传成功"
else
    echo "  ✗ 上传失败"
    exit 1
fi

# 上传 analysis_prompt_service.py
echo "[4/5] 上传 services/analysis_prompt_service.py..."
scp backend/services/analysis_prompt_service.py $SERVER_USER@$SERVER_IP:$SERVER_PATH/backend/services/
if [ $? -eq 0 ]; then
    echo "  ✓ 上传成功"
else
    echo "  ✗ 上传失败"
    exit 1
fi

# 上传 article_prompt_service.py
echo "[5/5] 上传 services/article_prompt_service.py..."
scp backend/services/article_prompt_service.py $SERVER_USER@$SERVER_IP:$SERVER_PATH/backend/services/
if [ $? -eq 0 ]; then
    echo "  ✓ 上传成功"
else
    echo "  ✗ 上传失败"
    exit 1
fi

echo ""
echo "========================================="
echo "文件上传完成！"
echo "========================================="
echo ""
echo "接下来需要在服务器上执行："
echo ""
echo "1. SSH 登录服务器:"
echo "   ssh $SERVER_USER@$SERVER_IP"
echo ""
echo "2. 检查当前运行的应用:"
echo "   ps aux | grep -E 'app\.py|app_with_upload\.py'"
echo ""
echo "3. 重启应用服务:"
echo "   sudo systemctl restart topn"
echo "   # 或者"
echo "   sudo supervisorctl restart topn"
echo ""
echo "4. 验证修复:"
echo "   curl -X POST http://localhost:8080/api/auth/login \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"username\":\"admin\",\"password\":\"TopN@2024\"}'"
echo ""
echo "详细部署指南请查看: SERVER_DEPLOYMENT_GUIDE.md"
echo "========================================="
