#!/bin/bash
# 清理旧发布历史系统的文件

echo "=========================================="
echo "清理旧发布历史系统"
echo "=========================================="

cd /home/u_topn/TOP_N

# 1. 备份旧数据库
echo ""
echo "[1/4] 备份旧数据库..."
if [ -f backend/publish_history.db ]; then
    cp backend/publish_history.db backend/publish_history.db.backup_$(date +%Y%m%d_%H%M%S)
    echo "✓ 已备份: backend/publish_history.db"
else
    echo "- 旧数据库不存在，跳过"
fi

# 2. 删除旧系统文件
echo ""
echo "[2/4] 删除旧系统文件..."

files_to_delete=(
    "backend/publish_history_api.py"
    "backend/init_publish_history_db.py"
    "backend/publish_history.db"
    "backend/models.py.bak_publish_history_fix"
)

for file in "${files_to_delete[@]}"; do
    if [ -f "$file" ]; then
        rm -f "$file"
        echo "✓ 已删除: $file"
    else
        echo "- 文件不存在: $file"
    fi
done

# 3. 清理测试和部署脚本
echo ""
echo "[3/4] 清理测试和部署脚本..."

test_scripts=(
    "scripts/test/test_publish_history_api.py"
    "scripts/fix/create_publish_history_step1.py"
    "scripts/deploy/deploy_publish_history_complete.py"
)

for script in "${test_scripts[@]}"; do
    if [ -f "$script" ]; then
        rm -f "$script"
        echo "✓ 已删除: $script"
    else
        echo "- 文件不存在: $script"
    fi
done

# 4. 显示保留的文件
echo ""
echo "[4/4] 保留的发布历史相关文件:"
echo "  ✓ templates/publish_history.html (前端页面)"
echo "  ✓ static/publish_history.js (前端脚本)"
echo "  ✓ data/topn.db (新的统一数据库)"
echo "  ✓ migrate_publish_history.py (迁移脚本，可留作参考)"

# 5. 统计
echo ""
echo "=========================================="
echo "清理完成！"
echo "=========================================="
echo ""
echo "新系统使用:"
echo "  - 数据库: data/topn.db"
echo "  - 模型: models.PublishHistory"
echo "  - API: blueprints/api.py:/api/publish_history"
echo "  - 前端: templates/publish_history.html + static/publish_history.js"
echo ""
echo "旧数据库备份位置: backend/publish_history.db.backup_*"
echo ""
