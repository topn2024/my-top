#!/bin/bash
# ============================================================================
# TOP_N Production Rollback Script
# ============================================================================
# Purpose: Quickly rollback to previous version if deployment fails
# Date: 2025-12-22
# ============================================================================

set -e

# Configuration
PROD_SERVER="39.105.12.124"
PROD_USER="u_topn"
PROD_DIR="/home/u_topn/TOP_N"
BACKUP_DIR="/home/u_topn/backups"

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

echo "=========================================="
echo -e "${RED}EMERGENCY ROLLBACK${NC}"
echo "=========================================="
echo ""
echo -e "${YELLOW}WARNING: This will restore the previous version${NC}"
echo ""

# Find latest backup
echo "Finding latest backup..."
LATEST_BACKUP=$(ssh ${PROD_USER}@${PROD_SERVER} "ls -t ${BACKUP_DIR}/pre_cleanup_*.tar.gz | head -1")

if [ -z "$LATEST_BACKUP" ]; then
    echo -e "${RED}ERROR: No backup found${NC}"
    exit 1
fi

echo "Latest backup: $LATEST_BACKUP"
echo ""
read -p "Proceed with rollback? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Rollback cancelled"
    exit 0
fi

echo ""
echo "Step 1: Stopping service..."
ssh ${PROD_USER}@${PROD_SERVER} << ENDSSH
    cd ${PROD_DIR}/backend

    if [ -f logs/gunicorn.pid ]; then
        PID=\$(cat logs/gunicorn.pid)
        echo "Stopping Gunicorn (PID: \$PID)..."
        kill -TERM \$PID
        sleep 2

        # Force kill if still running
        if ps -p \$PID > /dev/null; then
            kill -9 \$PID
            sleep 1
        fi
        echo "✓ Service stopped"
    fi
ENDSSH

echo ""
echo "Step 2: Restoring backup..."
ssh ${PROD_USER}@${PROD_SERVER} << ENDSSH
    cd ${PROD_DIR}

    # Extract backup
    echo "Extracting: $LATEST_BACKUP"
    tar -xzf $LATEST_BACKUP

    echo "✓ Backup restored"
ENDSSH

echo ""
echo "Step 3: Restarting service..."
ssh ${PROD_USER}@${PROD_SERVER} << ENDSSH
    cd ${PROD_DIR}/backend

    # Start Gunicorn
    nohup gunicorn -c gunicorn_config.py app_factory:app > logs/gunicorn_rollback.log 2>&1 &
    sleep 5

    # Check if running
    if [ -f logs/gunicorn.pid ]; then
        PID=\$(cat logs/gunicorn.pid)
        if ps -p \$PID > /dev/null; then
            echo "✓ Service restarted (PID: \$PID)"
        else
            echo "✗ Failed to start service"
            exit 1
        fi
    else
        echo "✗ No PID file created"
        exit 1
    fi
ENDSSH

echo ""
echo "Step 4: Verifying rollback..."
sleep 3

HEALTH_CHECK=$(ssh ${PROD_USER}@${PROD_SERVER} "curl -s http://localhost:8080/api/health || echo 'FAILED'")

if [[ "$HEALTH_CHECK" == *"FAILED"* ]]; then
    echo -e "${RED}✗ Health check failed after rollback${NC}"
    echo "Manual intervention required"
    exit 1
else
    echo -e "${GREEN}✓ Health check passed${NC}"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Rollback Completed${NC}"
echo "=========================================="
echo ""
echo "Service has been rolled back to previous version"
echo "Please investigate the issue before attempting redeployment"
echo ""
