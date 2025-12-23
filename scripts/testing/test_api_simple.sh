#!/bin/bash
# 简单测试发布历史API

echo "正在登录..."
COOKIE=$(curl -s -c - -X POST http://39.105.12.124/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | grep session | awk '{print $NF}')

echo "Cookie: $COOKIE"
echo ""
echo "正在获取发布历史..."
curl -s -b "session=$COOKIE" http://39.105.12.124/api/publish_history | python3 -m json.tool 2>/dev/null | head -50
