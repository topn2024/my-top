#!/bin/bash

# 服务器应用备份脚本
# 用途：在服务器上备份当前运行的应用

set -e

# 配置变量
BACKUP_DIR="/opt/backups"
APP_DIR="/opt/topn"  # 服务器上的应用目录
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="topn_server_backup_${TIMESTAMP}"
LOG_FILE="/var/log/topn_backup.log"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 检查并创建备份目录
check_backup_dir() {
    if [ ! -d "$BACKUP_DIR" ]; then
        log "创建备份目录: $BACKUP_DIR"
        sudo mkdir -p "$BACKUP_DIR"
        sudo chmod 755 "$BACKUP_DIR"
    fi
}

# 停止应用服务
stop_services() {
    log "正在停止应用服务..."
    sudo systemctl stop topn-app || true
    sudo systemctl stop topn-worker || true
    sleep 3
    log "应用服务已停止"
}

# 备份应用代码
backup_app_code() {
    log "开始备份应用代码..."
    sudo tar -czf "${BACKUP_DIR}/${BACKUP_NAME}_code.tar.gz" \
        -C "$APP_DIR" \
        --exclude='.git' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.idea' \
        --exclude='logs' \
        --exclude='uploads' \
        --exclude='*.log' \
        --exclude='venv' \
        --exclude='node_modules' \
        .
    log "应用代码备份完成: ${BACKUP_DIR}/${BACKUP_NAME}_code.tar.gz"
}

# 备份数据库
backup_database() {
    log "开始备份数据库..."
    if [ -f "$APP_DIR/data/topn.db" ]; then
        sudo cp "$APP_DIR/data/topn.db" "${BACKUP_DIR}/${BACKUP_NAME}_database.db"
        log "数据库备份完成: ${BACKUP_DIR}/${BACKUP_NAME}_database.db"
    else
        log "警告: 数据库文件不存在: $APP_DIR/data/topn.db"
    fi
}

# 备份配置文件
backup_configs() {
    log "开始备份配置文件..."
    sudo mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}_configs"

    # 备份systemd服务文件
    if [ -d "/etc/systemd/system" ]; then
        sudo find /etc/systemd/system -name "*topn*" -type f | \
        while read file; do
            sudo cp "$file" "${BACKUP_DIR}/${BACKUP_NAME}_configs/"
        done
    fi

    # 备份nginx配置
    if [ -f "/etc/nginx/sites-available/topn" ]; then
        sudo cp "/etc/nginx/sites-available/topn" "${BACKUP_DIR}/${BACKUP_NAME}_configs/"
    fi

    # 备份环境变量文件
    if [ -f "$APP_DIR/.env" ]; then
        sudo cp "$APP_DIR/.env" "${BACKUP_DIR}/${BACKUP_NAME}_configs/"
    fi

    log "配置文件备份完成: ${BACKUP_DIR}/${BACKUP_NAME}_configs/"
}

# 备份上传的文件
backup_uploads() {
    if [ -d "$APP_DIR/uploads" ]; then
        log "开始备份上传文件..."
        sudo tar -czf "${BACKUP_DIR}/${BACKUP_NAME}_uploads.tar.gz" -C "$APP_DIR" uploads/
        log "上传文件备份完成: ${BACKUP_DIR}/${BACKUP_NAME}_uploads.tar.gz"
    fi
}

# 生成备份清单
generate_manifest() {
    log "生成备份清单..."
    cat > "${BACKUP_DIR}/${BACKUP_NAME}_manifest.txt" << EOF
# 服务器备份清单
备份时间: $(date '+%Y-%m-%d %H:%M:%S')
备份名称: $BACKUP_NAME
应用目录: $APP_DIR

## 备份文件列表
EOF

    # 添加备份文件到清单
    echo "应用代码备份: ${BACKUP_NAME}_code.tar.gz" >> "${BACKUP_DIR}/${BACKUP_NAME}_manifest.txt"
    echo "数据库备份: ${BACKUP_NAME}_database.db" >> "${BACKUP_DIR}/${BACKUP_NAME}_manifest.txt"
    echo "配置文件备份: ${BACKUP_NAME}_configs/" >> "${BACKUP_DIR}/${BACKUP_NAME}_manifest.txt"

    if [ -f "${BACKUP_DIR}/${BACKUP_NAME}_uploads.tar.gz" ]; then
        echo "上传文件备份: ${BACKUP_NAME}_uploads.tar.gz" >> "${BACKUP_DIR}/${BACKUP_NAME}_manifest.txt"
    fi

    # 添加文件大小信息
    echo "" >> "${BACKUP_DIR}/${BACKUP_NAME}_manifest.txt"
    echo "## 文件大小信息" >> "${BACKUP_DIR}/${BACKUP_NAME}_manifest.txt"

    for file in "${BACKUP_DIR}/${BACKUP_NAME}_code.tar.gz" "${BACKUP_DIR}/${BACKUP_NAME}_database.db"; do
        if [ -f "$file" ]; then
            size=$(du -h "$file" | cut -f1)
            echo "$(basename "$file"): $size" >> "${BACKUP_DIR}/${BACKUP_NAME}_manifest.txt"
        fi
    done

    log "备份清单生成完成: ${BACKUP_DIR}/${BACKUP_NAME}_manifest.txt"
}

# 启动应用服务
start_services() {
    log "正在启动应用服务..."
    sudo systemctl start topn-app || true
    sudo systemctl start topn-worker || true
    sleep 3
    log "应用服务已启动"
}

# 清理旧备份
cleanup_old_backups() {
    log "清理30天前的备份..."
    find "$BACKUP_DIR" -name "topn_server_backup_*" -type d -mtime +30 -exec rm -rf {} \; 2>/dev/null || true
    find "$BACKUP_DIR" -name "topn_server_backup_*" -type f -mtime +30 -delete 2>/dev/null || true
    log "旧备份清理完成"
}

# 主函数
main() {
    log "=== 开始服务器备份 ==="

    check_backup_dir
    stop_services
    backup_app_code
    backup_database
    backup_configs
    backup_uploads
    generate_manifest
    start_services
    cleanup_old_backups

    log "=== 服务器备份完成 ==="
    log "备份位置: $BACKUP_DIR"
    log "备份名称: $BACKUP_NAME"
    log "恢复方法: 参考备份清单文件"

    # 显示备份文件
    echo ""
    echo "生成的备份文件:"
    ls -la "$BACKUP_DIR"/"${BACKUP_NAME}"*
}

# 执行主函数
main "$@"