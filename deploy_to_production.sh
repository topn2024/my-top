#!/bin/bash
# ============================================================================
# TOP_N Production Deployment Script
# ============================================================================
# Purpose: Deploy architecture cleanup changes to production server
# Date: 2025-12-22
# Server: 39.105.12.124
# ============================================================================

set -e  # Exit on error

echo "=========================================="
echo "TOP_N Production Deployment"
echo "=========================================="
echo ""

# Configuration
PROD_SERVER="39.105.12.124"
PROD_USER="u_topn"
PROD_DIR="/home/u_topn/TOP_N"
BACKUP_DIR="/home/u_topn/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Step 1: Pre-deployment Checklist${NC}"
echo "-----------------------------------"
echo "Please confirm the following:"
echo "  [1] All tests passed locally"
echo "  [2] Code committed to Git"
echo "  [3] You have SSH access to production server"
echo "  [4] Backup plan is ready"
echo ""
read -p "Continue with deployment? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Deployment cancelled."
    exit 0
fi

echo ""
echo -e "${YELLOW}Step 2: Creating Backup${NC}"
echo "-----------------------------------"
ssh ${PROD_USER}@${PROD_SERVER} << 'ENDSSH'
    set -e
    cd /home/u_topn/TOP_N

    # Create backup directory if not exists
    mkdir -p ../backups

    # Backup current code
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    tar -czf ../backups/pre_cleanup_${TIMESTAMP}.tar.gz backend/

    echo "Backup created: pre_cleanup_${TIMESTAMP}.tar.gz"
    ls -lh ../backups/pre_cleanup_${TIMESTAMP}.tar.gz
ENDSSH

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Backup completed successfully${NC}"
else
    echo -e "${RED}✗ Backup failed${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 3: Pulling New Code${NC}"
echo "-----------------------------------"
ssh ${PROD_USER}@${PROD_SERVER} << 'ENDSSH'
    set -e
    cd /home/u_topn/TOP_N

    # Fetch latest changes
    git fetch origin main

    # Show what will be updated
    echo "Changes to be pulled:"
    git log HEAD..origin/main --oneline

    # Pull changes
    git pull origin main

    echo "Code updated successfully"
ENDSSH

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Code pulled successfully${NC}"
else
    echo -e "${RED}✗ Git pull failed${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 4: Environment Variable Setup${NC}"
echo "-----------------------------------"
echo "Checking if .env file exists on production..."

ssh ${PROD_USER}@${PROD_SERVER} << 'ENDSSH'
    set -e
    cd /home/u_topn/TOP_N

    if [ ! -f .env ]; then
        echo "Creating .env file from template..."
        cp .env.template .env
        echo ""
        echo "IMPORTANT: Please edit .env file and set the following variables:"
        echo "  - TOPN_SECRET_KEY"
        echo "  - ZHIPU_API_KEY"
        echo "  - QIANWEN_API_KEY"
        echo "  - ENCRYPTION_KEY"
        echo ""
        echo "You can generate secure keys with:"
        echo "  python3 -c \"import secrets; print(secrets.token_hex(32))\""
        echo ""
        exit 1
    else
        echo ".env file exists"
        echo "Checking for required variables..."

        missing=""
        if ! grep -q "^TOPN_SECRET_KEY=" .env || grep -q "^TOPN_SECRET_KEY=请更改" .env; then
            missing="${missing}TOPN_SECRET_KEY "
        fi
        if ! grep -q "^ZHIPU_API_KEY=" .env || grep -q "^ZHIPU_API_KEY=your_zhipu" .env; then
            missing="${missing}ZHIPU_API_KEY "
        fi

        if [ -n "$missing" ]; then
            echo "ERROR: Missing or default values for: $missing"
            echo "Please edit .env file before continuing"
            exit 1
        fi

        echo "✓ Required environment variables are set"
    fi
ENDSSH

if [ $? -ne 0 ]; then
    echo ""
    echo -e "${YELLOW}Action Required:${NC}"
    echo "1. SSH to production: ssh ${PROD_USER}@${PROD_SERVER}"
    echo "2. Edit .env file: cd ${PROD_DIR} && nano .env"
    echo "3. Set required variables"
    echo "4. Run this script again"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 5: Configuration Validation${NC}"
echo "-----------------------------------"
ssh ${PROD_USER}@${PROD_SERVER} << 'ENDSSH'
    set -e
    cd /home/u_topn/TOP_N/backend

    # Test configuration loading
    python3 -c "from config import get_config; cfg = get_config('production'); print('Configuration loaded successfully')"

    # Test imports
    python3 -c "from auth import init_permissions; print('Auth module imports OK')"
    python3 -c "from blueprints.api import api_bp; print('API blueprint imports OK')"
    python3 -c "from blueprints.api_retry import api_retry_bp; print('Retry blueprint imports OK')"

    echo "✓ All imports successful"
ENDSSH

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Configuration validation passed${NC}"
else
    echo -e "${RED}✗ Configuration validation failed${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 6: Graceful Service Restart${NC}"
echo "-----------------------------------"
ssh ${PROD_USER}@${PROD_SERVER} << 'ENDSSH'
    set -e
    cd /home/u_topn/TOP_N/backend

    # Find Gunicorn PID
    if [ -f logs/gunicorn.pid ]; then
        OLD_PID=$(cat logs/gunicorn.pid)
        echo "Found Gunicorn process: PID $OLD_PID"

        # Graceful reload (HUP signal)
        echo "Sending HUP signal for graceful reload..."
        kill -HUP $OLD_PID

        sleep 3

        # Check if process is still running
        if ps -p $OLD_PID > /dev/null; then
            echo "✓ Gunicorn reloaded successfully"
        else
            echo "Process stopped, restarting..."
            nohup gunicorn -c gunicorn_config.py app_factory:app > logs/gunicorn_startup.log 2>&1 &
            sleep 5
        fi
    else
        echo "No PID file found, starting Gunicorn..."
        nohup gunicorn -c gunicorn_config.py app_factory:app > logs/gunicorn_startup.log 2>&1 &
        sleep 5
    fi

    # Verify service is running
    NEW_PID=$(cat logs/gunicorn.pid 2>/dev/null || echo "")
    if [ -n "$NEW_PID" ]; then
        echo "✓ Service running with PID: $NEW_PID"
    else
        echo "✗ Failed to start service"
        exit 1
    fi
ENDSSH

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Service restarted successfully${NC}"
else
    echo -e "${RED}✗ Service restart failed${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 7: Post-Deployment Verification${NC}"
echo "-----------------------------------"

# Wait for service to be fully ready
echo "Waiting 5 seconds for service to initialize..."
sleep 5

# Test health endpoint
echo "Testing health endpoint..."
HEALTH_CHECK=$(ssh ${PROD_USER}@${PROD_SERVER} "curl -s http://localhost:8080/api/health || echo 'FAILED'")

if [[ "$HEALTH_CHECK" == *"FAILED"* ]]; then
    echo -e "${RED}✗ Health check failed${NC}"
    echo "Response: $HEALTH_CHECK"
    exit 1
else
    echo -e "${GREEN}✓ Health check passed${NC}"
fi

# Test new routes
echo ""
echo "Testing new routes (requires authentication)..."
echo "  - /api/platforms (GET)"
echo "  - /api/accounts/import (POST)"
echo "  - /api/csdn/login (POST)"

ssh ${PROD_USER}@${PROD_SERVER} << 'ENDSSH'
    # Test platforms endpoint (should work without auth or return 401)
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/api/platforms)
    echo "  /api/platforms: HTTP $STATUS"

    # Test CSDN login endpoint (should return 400/401, not 404)
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8080/api/csdn/login)
    echo "  /api/csdn/login: HTTP $STATUS"

    # Test retry publish endpoint
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8080/api/retry_publish/1)
    echo "  /api/retry_publish/1: HTTP $STATUS"
ENDSSH

echo ""
echo -e "${YELLOW}Step 8: Log Check${NC}"
echo "-----------------------------------"
ssh ${PROD_USER}@${PROD_SERVER} << 'ENDSSH'
    cd /home/u_topn/TOP_N/backend

    echo "Last 20 lines of application log:"
    echo "---"
    tail -n 20 logs/all.log
    echo ""

    echo "Checking for errors in last 100 lines..."
    ERROR_COUNT=$(tail -n 100 logs/all.log | grep -i error | wc -l || echo "0")
    echo "Found $ERROR_COUNT error entries"

    if [ "$ERROR_COUNT" -gt 0 ]; then
        echo "Recent errors:"
        tail -n 100 logs/all.log | grep -i error | tail -5
    fi
ENDSSH

echo ""
echo "=========================================="
echo -e "${GREEN}Deployment Completed${NC}"
echo "=========================================="
echo ""
echo "Next Steps:"
echo "  1. Monitor logs: ssh ${PROD_USER}@${PROD_SERVER} 'tail -f ${PROD_DIR}/backend/logs/all.log'"
echo "  2. Test functionality through web interface"
echo "  3. Monitor for 48 hours (Phase P5)"
echo "  4. If issues occur, run rollback script"
echo ""
echo "Rollback command:"
echo "  ssh ${PROD_USER}@${PROD_SERVER} 'cd ${PROD_DIR} && tar -xzf ../backups/pre_cleanup_*.tar.gz && kill -HUP \$(cat backend/logs/gunicorn.pid)'"
echo ""
