#!/bin/bash
# 部署前备份脚本 - 在服务器上执行
# 用途：创建完整备份以便回滚

set -e  # 遇到错误立即退出

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/u_topn/TOP_N/backups/${TIMESTAMP}"

echo "========================================="
echo "创建部署前备份: ${BACKUP_DIR}"
echo "========================================="

# 1. 创建备份目录
mkdir -p "${BACKUP_DIR}"

# 2. 备份后端代码
echo "[1/5] 备份后端代码..."
cp -r /home/u_topn/TOP_N/backend "${BACKUP_DIR}/"

# 3. 备份数据库
echo "[2/5] 备份数据库..."
cp /home/u_topn/TOP_N/data/topn.db "${BACKUP_DIR}/"

# 4. 备份systemd配置
echo "[3/5] 备份systemd配置..."
sudo cp /etc/systemd/system/topn.service "${BACKUP_DIR}/"

# 5. 备份gunicorn配置
echo "[4/5] 备份gunicorn配置..."
cp /home/u_topn/TOP_N/gunicorn_config.py "${BACKUP_DIR}/"

# 6. 记录当前服务状态
echo "[5/5] 记录服务状态..."
sudo systemctl status topn.service --no-pager > "${BACKUP_DIR}/service_status.txt" 2>&1 || true
ps aux | grep gunicorn | grep -v grep > "${BACKUP_DIR}/process_list.txt" || true

# 7. 创建备份信息文件
cat > "${BACKUP_DIR}/backup_info.txt" << EOF
备份时间: ${TIMESTAMP}
备份路径: ${BACKUP_DIR}
备份内容:
  - backend/ (后端代码)
  - topn.db (数据库)
  - topn.service (systemd配置)
  - gunicorn_config.py (Gunicorn配置)
  - service_status.txt (服务状态)
  - process_list.txt (进程列表)

恢复方法:
  bash rollback_deployment.sh ${TIMESTAMP}
EOF

echo ""
echo "========================================="
echo "备份完成: ${BACKUP_DIR}"
echo "备份大小: $(du -sh ${BACKUP_DIR} | cut -f1)"
echo "========================================="
echo ""
echo "备份ID: ${TIMESTAMP}"
echo "请记录此ID用于回滚！"
