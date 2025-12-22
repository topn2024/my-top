#!/bin/bash
# 部署回滚脚本
# 用途：快速回滚到部署前的状态

set -e

SERVER="u_topn@39.105.12.124"
BACKUP_ID="$1"

if [ -z "${BACKUP_ID}" ]; then
    echo "错误: 请提供备份ID"
    echo "用法: $0 <BACKUP_ID>"
    echo ""
    echo "可用备份:"
    ssh ${SERVER} "ls -lt /home/u_topn/TOP_N/backups/ | head -10"
    exit 1
fi

BACKUP_DIR="/home/u_topn/TOP_N/backups/${BACKUP_ID}"

echo "========================================="
echo "回滚部署: ${BACKUP_ID}"
echo "========================================="
echo ""

# 确认回滚
read -p "确认要回滚到备份 ${BACKUP_ID}? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "回滚已取消"
    exit 0
fi

# 在服务器上执行回滚
ssh ${SERVER} << ENDSSH
set -e

BACKUP_DIR="${BACKUP_DIR}"

# 1. 检查备份是否存在
if [ ! -d "\${BACKUP_DIR}" ]; then
    echo "错误: 备份目录不存在: \${BACKUP_DIR}"
    exit 1
fi

echo "[步骤 1/5] 停止服务..."
sudo systemctl stop topn.service
sleep 3

echo ""
echo "[步骤 2/5] 恢复后端代码..."
rm -rf /home/u_topn/TOP_N/backend.old
mv /home/u_topn/TOP_N/backend /home/u_topn/TOP_N/backend.old
cp -r "\${BACKUP_DIR}/backend" /home/u_topn/TOP_N/

echo ""
echo "[步骤 3/5] 恢复数据库..."
cp /home/u_topn/TOP_N/data/topn.db /home/u_topn/TOP_N/data/topn.db.before_rollback
cp "\${BACKUP_DIR}/topn.db" /home/u_topn/TOP_N/data/

echo ""
echo "[步骤 4/5] 恢复systemd配置..."
sudo cp "\${BACKUP_DIR}/topn.service" /etc/systemd/system/
sudo systemctl daemon-reload

echo ""
echo "[步骤 5/5] 启动服务..."
sudo systemctl start topn.service
sleep 5

# 验证服务
if sudo systemctl is-active --quiet topn.service; then
    echo ""
    echo "========================================="
    echo "回滚完成！服务正常运行"
    echo "========================================="
    echo ""
    echo "健康检查:"
    curl -s http://localhost:8080/api/health || echo "健康检查失败"
    echo ""
else
    echo ""
    echo "错误: 服务启动失败！"
    sudo systemctl status topn.service --no-pager
    exit 1
fi

echo ""
echo "回滚的文件已保存:"
echo "  - backend.old (失败的部署)"
echo "  - data/topn.db.before_rollback (回滚前的数据库)"
ENDSSH

echo ""
echo "回滚完成！"
echo ""
echo "建议接下来:"
echo "  1. 检查服务日志"
echo "  2. 验证功能正常"
echo "  3. 分析部署失败原因"
