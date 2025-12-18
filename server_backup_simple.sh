#!/bin/bash

# 简化的服务器备份脚本
# 适用于快速备份到GitHub同步

set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_TAG="server_backup_${TIMESTAMP}"

echo "=== 服务器备份开始 [$TIMESTAMP] ==="

# 1. 检查git状态
echo "检查Git状态..."
cd /opt/topn
git status

# 2. 添加所有更改
echo "添加更改..."
git add .

# 3. 创建备份提交
echo "创建备份提交..."
git commit -m "Server backup ${TIMESTAMP}

- Automated server backup before refactoring
- Runtime state and data backup
- Safe rollback point created

Backup tag: ${BACKUP_TAG}"

# 4. 创建备份标签
echo "创建备份标签..."
git tag -a "${BACKUP_TAG}" -m "Server backup ${TIMESTAMP}"

# 5. 推送到远程仓库
echo "推送到GitHub..."
git push origin main
git push origin "${BACKUP_TAG}"

# 6. 备份数据库文件
echo "备份数据库..."
cp data/topn.db "data/topn.db.backup_${TIMESTAMP}"
git add data/topn.db.backup_${TIMESTAMP}
git commit -m "Add database backup ${TIMESTAMP}"
git push origin main

echo "=== 服务器备份完成 ==="
echo "备份标签: ${BACKUP_TAG}"
echo "恢复命令: git checkout ${BACKUP_TAG}"