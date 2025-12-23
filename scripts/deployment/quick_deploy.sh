#!/bin/bash
# 快速部署指定文件到服务器

if [ $# -eq 0 ]; then
    echo "用法: ./quick_deploy.sh <文件路径> [文件路径2] ..."
    echo ""
    echo "示例:"
    echo "  ./quick_deploy.sh templates/index.html"
    echo "  ./quick_deploy.sh static/analysis.js backend/app_factory.py"
    echo ""
    exit 1
fi

SERVER="u_topn@39.105.12.124"
REMOTE_PATH="/home/u_topn/TOP_N"
NEED_RESTART=false

echo "========================================="
echo "快速部署脚本"
echo "========================================="
echo ""

# 检查所有文件
for FILE in "$@"; do
    if [ ! -f "$FILE" ]; then
        echo "❌ 错误: 文件不存在 - $FILE"
        exit 1
    fi
done

# 检查 Git 状态
UNCOMMITTED=$(git status --porcelain | grep -E "$(echo "$@" | tr ' ' '|')")
if [ -n "$UNCOMMITTED" ]; then
    echo "⚠️  警告: 以下文件未提交到 Git:"
    echo "$UNCOMMITTED"
    echo ""
    read -p "是否继续部署? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "部署已取消"
        exit 1
    fi
fi

echo ""
echo "开始部署..."
echo ""

# 部署每个文件
for FILE in "$@"; do
    echo "[部署] $FILE"

    # 上传文件
    scp "$FILE" "$SERVER:$REMOTE_PATH/$FILE"

    if [ $? -eq 0 ]; then
        echo "  ✓ 上传成功"

        # 检查是否需要重启服务
        if [[ "$FILE" == backend/*.py ]]; then
            NEED_RESTART=true
        fi
    else
        echo "  ✗ 上传失败"
        exit 1
    fi
done

echo ""

# 如果修改了后端文件，询问是否重启服务
if [ "$NEED_RESTART" = true ]; then
    echo "检测到后端文件修改"
    read -p "是否重启 Gunicorn 服务? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "重启服务中..."
        ssh "$SERVER" "killall -9 gunicorn && cd $REMOTE_PATH && ./start_service.sh"
        echo "✓ 服务已重启"
    fi
fi

echo ""
echo "========================================="
echo "部署完成！"
echo "========================================="
echo ""
echo "建议操作:"
echo "1. 访问 http://39.105.12.124 验证功能"
echo "2. 清除浏览器缓存 (Ctrl+Shift+Delete)"
echo "3. 检查浏览器控制台是否有错误"
echo ""
