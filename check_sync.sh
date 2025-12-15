#!/bin/bash
# 检查本地和服务器文件是否一致

SERVER="u_topn@39.105.12.124"
REMOTE_PATH="/home/u_topn/TOP_N"

# 关键文件列表
FILES=(
    "templates/index.html"
    "templates/analysis.html"
    "templates/admin_dashboard.html"
    "templates/login.html"
    "static/analysis.js"
    "static/input.js"
    "static/publish.js"
    "backend/app.py"
    "backend/app_factory.py"
    "backend/blueprints/auth.py"
    "backend/blueprints/api.py"
)

echo "========================================="
echo "本地与服务器文件同步检查"
echo "========================================="
echo ""
echo "检查时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

DIFF_COUNT=0
MISSING_COUNT=0
MATCH_COUNT=0

for file in "${FILES[@]}"; do
    printf "%-50s" "$file"

    # 检查本地文件是否存在
    if [ ! -f "$file" ]; then
        echo "⚠️  本地不存在"
        ((MISSING_COUNT++))
        continue
    fi

    # 下载服务器版本到临时文件
    TMP_FILE="/tmp/server_$(basename $file)_$$"
    scp -q "$SERVER:$REMOTE_PATH/$file" "$TMP_FILE" 2>/dev/null

    if [ $? -ne 0 ]; then
        echo "❌ 服务器不存在"
        ((MISSING_COUNT++))
        rm -f "$TMP_FILE"
        continue
    fi

    # 对比文件
    if diff -q "$file" "$TMP_FILE" > /dev/null 2>&1; then
        echo "✓ 一致"
        ((MATCH_COUNT++))
    else
        echo "⚠️  不一致"
        ((DIFF_COUNT++))

        # 保存差异文件供后续查看
        DIFF_FILE="/tmp/diff_$(basename $file)_$$"
        diff -u "$file" "$TMP_FILE" > "$DIFF_FILE"
        echo "  → 差异已保存到: $DIFF_FILE"
        echo "  → 查看差异: diff -u $file $TMP_FILE | head -30"
    fi

    rm -f "$TMP_FILE"
done

echo ""
echo "========================================="
echo "检查结果汇总"
echo "========================================="
echo "✓ 一致: $MATCH_COUNT 个文件"
echo "⚠️  不一致: $DIFF_COUNT 个文件"
echo "❌ 缺失: $MISSING_COUNT 个文件"
echo ""

if [ $DIFF_COUNT -gt 0 ]; then
    echo "⚠️  发现不一致的文件！"
    echo ""
    echo "建议操作:"
    echo "1. 检查差异文件内容"
    echo "2. 决定保留本地版本还是服务器版本"
    echo "3. 同步文件并提交到 Git"
    echo ""
    echo "示例命令:"
    echo "  # 如果保留服务器版本:"
    echo "  scp u_topn@39.105.12.124:/home/u_topn/TOP_N/<file> <local-file>"
    echo "  git add <local-file>"
    echo "  git commit -m \"Sync from server: <description>\""
    echo ""
    echo "  # 如果保留本地版本:"
    echo "  ./quick_deploy.sh <local-file>"
    echo ""
    exit 1
else
    echo "✅ 所有文件都已同步！"
    exit 0
fi
