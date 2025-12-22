#!/bin/bash
# 生产环境验证脚本
# 用途：验证部署后的功能是否正常

SERVER="u_topn@39.105.12.124"

echo "========================================="
echo "生产环境验证"
echo "========================================="
echo ""

# 1. 服务状态
echo "[检查 1/6] 服务状态..."
ssh ${SERVER} << 'ENDSSH'
if sudo systemctl is-active --quiet topn.service; then
    echo "  [PASS] 服务运行中"
else
    echo "  [FAIL] 服务未运行"
    exit 1
fi
ENDSSH

# 2. 进程检查
echo ""
echo "[检查 2/6] 进程检查..."
PROCESS_COUNT=$(ssh ${SERVER} "ps aux | grep 'gunicorn.*app:app' | grep -v grep | wc -l")
echo "  Gunicorn workers: ${PROCESS_COUNT}"
if [ "${PROCESS_COUNT}" -gt 0 ]; then
    echo "  [PASS] 进程正常"
else
    echo "  [FAIL] 未找到gunicorn进程"
fi

# 3. 健康检查
echo ""
echo "[检查 3/6] 健康检查..."
HEALTH=$(ssh ${SERVER} "curl -s http://localhost:8080/api/health")
echo "  响应: ${HEALTH}"
if echo "${HEALTH}" | grep -q "ok"; then
    echo "  [PASS] 健康检查通过"
else
    echo "  [FAIL] 健康检查失败"
fi

# 4. 验证6个修复的路由
echo ""
echo "[检查 4/6] 验证修复的路由 (应返回401而非404)..."
ssh ${SERVER} << 'ENDSSH'
routes=(
    "POST http://localhost:8080/api/accounts/1/test"
    "POST http://localhost:8080/api/accounts/import"
    "POST http://localhost:8080/api/csdn/login"
    "POST http://localhost:8080/api/csdn/check_login"
    "POST http://localhost:8080/api/csdn/publish"
    "GET http://localhost:8080/api/platforms"
)

failed=0
for route in "${routes[@]}"; do
    method=$(echo $route | cut -d' ' -f1)
    url=$(echo $route | cut -d' ' -f2)
    code=$(curl -s -o /dev/null -w '%{http_code}' -X $method $url)

    path=$(echo $url | sed 's|http://localhost:8080||')
    if [ "$code" = "404" ]; then
        echo "  [FAIL] $path -> $code (应为401/400/405)"
        ((failed++))
    else
        echo "  [PASS] $path -> $code"
    fi
done

if [ $failed -eq 0 ]; then
    echo "  所有路由验证通过"
else
    echo "  有 $failed 个路由失败"
fi
ENDSSH

# 5. 数据库表检查
echo ""
echo "[检查 5/6] 数据库表检查..."
TABLE_COUNT=$(ssh ${SERVER} "cd /home/u_topn/TOP_N/backend && python3 -c 'from models import Base; print(len(Base.metadata.tables))' 2>/dev/null")
echo "  数据库表数量: ${TABLE_COUNT}"
if [ "${TABLE_COUNT}" = "15" ]; then
    echo "  [PASS] 表数量正确"
else
    echo "  [WARN] 预期15个表，实际${TABLE_COUNT}个"
fi

# 6. 错误日志检查
echo ""
echo "[检查 6/6] 最近错误日志..."
ssh ${SERVER} << 'ENDSSH'
recent_errors=$(tail -100 /home/u_topn/TOP_N/logs/gunicorn_error.log 2>/dev/null | grep -i error | wc -l)
echo "  最近100行中的错误: ${recent_errors}"
if [ "${recent_errors}" -lt 5 ]; then
    echo "  [PASS] 错误日志正常"
else
    echo "  [WARN] 错误较多，需要检查"
    echo "  最近的错误:"
    tail -100 /home/u_topn/TOP_N/logs/gunicorn_error.log | grep -i error | tail -5
fi
ENDSSH

echo ""
echo "========================================="
echo "验证完成"
echo "========================================="
echo ""
echo "详细日志查看:"
echo "  ssh ${SERVER} 'tail -f /home/u_topn/TOP_N/logs/gunicorn_error.log'"
