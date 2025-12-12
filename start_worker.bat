@echo off
chcp 65001 >nul
echo ============================================================
echo    TOP_N RQ Worker 启动脚本 (Windows)
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/4] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python未安装或不在PATH中
    echo 请安装Python 3.7+并添加到PATH
    pause
    exit /b 1
)
python --version
echo.

echo [2/4] 安装/更新依赖...
python -m pip install --quiet --upgrade redis rq DrissionPage
if errorlevel 1 (
    echo ❌ 依赖安装失败
    pause
    exit /b 1
)
echo ✅ 依赖已安装
echo.

echo [3/4] 检查Redis服务...
python -c "import redis; r=redis.Redis(host='localhost',port=6379); r.ping(); print('✅ Redis运行正常')" 2>nul
if errorlevel 1 (
    echo ❌ Redis未运行
    echo.
    echo 请先启动Redis服务:
    echo   1. 下载 Redis for Windows: https://github.com/tporadowski/redis/releases
    echo   2. 解压后运行 redis-server.exe
    echo   3. 或者使用WSL: sudo service redis-server start
    echo.
    pause
    exit /b 1
)
echo.

echo [4/4] 启动RQ Worker...
echo 监听队列: default, user:*
echo Redis: localhost:6379/0
echo 日志输出: 控制台
echo.
echo ============================================================
echo Worker运行中... (按Ctrl+C停止)
echo ============================================================
echo.

cd backend
python -m rq worker default user:* --url redis://localhost:6379/0 --name worker-windows

echo.
echo Worker已停止
pause
