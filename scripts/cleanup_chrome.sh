#!/bin/bash
# Chrome进程清理脚本

echo "=== Chrome进程清理脚本 ==="
echo "时间: $(date)"

# 查找所有DrissionPage相关的Chrome进程
CHROME_PIDS=$(ps aux | grep -E 'chrome.*(DrissionPage|remote-debugging)' | grep -v grep | awk '{print $2}')

if [ -z "$CHROME_PIDS" ]; then
    echo "✓ 没有发现僵尸Chrome进程"
else
    echo "发现以下Chrome进程:"
    ps aux | grep -E 'chrome.*(DrissionPage|remote-debugging)' | grep -v grep | head -5

    echo ""
    echo "开始清理..."
    for pid in $CHROME_PIDS; do
        echo "  杀死进程: $pid"
        kill -9 $pid 2>/dev/null || true
    done

    sleep 1
    echo "✓ 清理完成"
fi

echo ""
echo "当前内存使用:"
free -h

echo ""
echo "当前Chrome进程数: $(ps aux | grep chrome | grep -v grep | wc -l)"
