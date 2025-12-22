#!/bin/bash
# ============================================================================
# TOP_N Production Verification Script
# ============================================================================
# Purpose: Verify all routes are working correctly after deployment
# Date: 2025-12-22
# ============================================================================

PROD_SERVER="39.105.12.124"
PROD_USER="u_topn"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "=========================================="
echo "TOP_N Production Verification"
echo "=========================================="
echo ""

# Counter for pass/fail
TOTAL=0
PASSED=0
FAILED=0

test_endpoint() {
    local method=$1
    local path=$2
    local description=$3
    local expected_codes=$4  # Space-separated list like "200 401"

    TOTAL=$((TOTAL + 1))

    if [ "$method" = "GET" ]; then
        STATUS=$(ssh ${PROD_USER}@${PROD_SERVER} "curl -s -o /dev/null -w '%{http_code}' http://localhost:8080${path}" 2>/dev/null)
    else
        STATUS=$(ssh ${PROD_USER}@${PROD_SERVER} "curl -s -o /dev/null -w '%{http_code}' -X ${method} http://localhost:8080${path}" 2>/dev/null)
    fi

    # Check if status is in expected codes
    if [[ " $expected_codes " =~ " $STATUS " ]]; then
        echo -e "  ${GREEN}✓${NC} ${description}: HTTP ${STATUS}"
        PASSED=$((PASSED + 1))
    else
        echo -e "  ${RED}✗${NC} ${description}: HTTP ${STATUS} (expected: ${expected_codes})"
        FAILED=$((FAILED + 1))
    fi
}

echo -e "${YELLOW}Testing Core Routes${NC}"
echo "-----------------------------------"
test_endpoint "GET" "/api/health" "Health check" "200"
test_endpoint "GET" "/" "Home page" "200 302"

echo ""
echo -e "${YELLOW}Testing Account Management Routes${NC}"
echo "-----------------------------------"
test_endpoint "GET" "/api/accounts" "List accounts" "200 401"
test_endpoint "POST" "/api/accounts" "Create account" "400 401"
test_endpoint "POST" "/api/accounts/1/test" "Test account (NEW)" "400 401 404"
test_endpoint "POST" "/api/accounts/import" "Import accounts (NEW)" "400 401"

echo ""
echo -e "${YELLOW}Testing CSDN Routes (NEW)${NC}"
echo "-----------------------------------"
test_endpoint "POST" "/api/csdn/login" "CSDN login" "400 401"
test_endpoint "POST" "/api/csdn/check_login" "CSDN check login" "400 401"
test_endpoint "POST" "/api/csdn/publish" "CSDN publish" "400 401"

echo ""
echo -e "${YELLOW}Testing Platform Routes${NC}"
echo "-----------------------------------"
test_endpoint "GET" "/api/platforms" "Get platforms (NEW)" "200 401"

echo ""
echo -e "${YELLOW}Testing Publish Routes${NC}"
echo "-----------------------------------"
test_endpoint "GET" "/api/history" "Publish history" "200 401"
test_endpoint "POST" "/api/retry_publish/1" "Retry publish (NEW)" "400 401 404"

echo ""
echo -e "${YELLOW}Testing Article Routes${NC}"
echo "-----------------------------------"
test_endpoint "GET" "/api/articles" "List articles" "200 401"
test_endpoint "POST" "/api/articles" "Create article" "400 401"

echo ""
echo -e "${YELLOW}Testing Authentication Routes${NC}"
echo "-----------------------------------"
test_endpoint "GET" "/auth/login" "Login page" "200 302"
test_endpoint "GET" "/auth/logout" "Logout" "302"

echo ""
echo "=========================================="
echo "Verification Summary"
echo "=========================================="
echo -e "Total tests: ${TOTAL}"
echo -e "Passed: ${GREEN}${PASSED}${NC}"
echo -e "Failed: ${RED}${FAILED}${NC}"

if [ $FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ All tests passed${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}✗ Some tests failed${NC}"
    echo "Please check the logs for details"
    exit 1
fi
