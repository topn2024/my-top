#!/bin/bash
# AI 服务商快速切换脚本

PROVIDER=$1

if [ -z "$PROVIDER" ]; then
    echo "Usage: $0 [zhipu|qianwen]"
    echo ""
    echo "Current provider:"
    python -c "import sys; sys.path.insert(0, 'backend'); from config import Config; print(f'  {Config.DEFAULT_AI_PROVIDER}')" 2>/dev/null || echo "  Unable to determine"
    exit 1
fi

if [ "$PROVIDER" != "zhipu" ] && [ "$PROVIDER" != "qianwen" ]; then
    echo "Error: Invalid provider '$PROVIDER'"
    echo "Valid options: zhipu, qianwen"
    exit 1
fi

echo "============================================================"
echo "AI Provider Switcher"
echo "============================================================"
echo ""
echo "Switching to: $PROVIDER"
echo ""

# 设置环境变量
export AI_PROVIDER=$PROVIDER

# 验证切换
echo "Verifying configuration..."
python test_zhipu_config.py 2>&1 | grep -E "Default AI Provider:|Active Provider:" | head -2

echo ""
echo "============================================================"
echo "Environment variable set:"
echo "  export AI_PROVIDER=$PROVIDER"
echo ""
echo "To make this permanent, add to your shell profile:"
echo "  echo 'export AI_PROVIDER=$PROVIDER' >> ~/.bashrc"
echo "  source ~/.bashrc"
echo "============================================================"
