#!/bin/bash

# TOP_N 启动脚本

cd "$(dirname "$0")/backend"

echo "启动 TOP_N 平台..."
echo "访问地址: http://localhost:8080"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3"
    exit 1
fi

# 安装依赖（如果需要）
if [ ! -d "../venv" ]; then
    echo "首次运行，安装依赖..."
    cd ..
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd backend
fi

# 激活虚拟环境
cd ..
source venv/bin/activate
cd backend

# 启动应用
python3 app.py
