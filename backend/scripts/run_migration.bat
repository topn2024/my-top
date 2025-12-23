@echo off
chcp 65001 >nul
echo ===============================================================================
echo 发布历史数据整合迁移
echo ===============================================================================
echo.

REM 设置路径
set SCRIPT_DIR=%~dp0
set DB_PATH=%SCRIPT_DIR%..\data\topn.db
set BACKUP_PATH=%SCRIPT_DIR%..\data\topn.db.backup_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set BACKUP_PATH=%BACKUP_PATH: =0%

echo 第1步：备份数据库
echo -------------------------------------------------------------------------------
if exist "%DB_PATH%" (
    echo 正在备份数据库...
    copy "%DB_PATH%" "%BACKUP_PATH%"
    if %errorlevel% equ 0 (
        echo ✓ 数据库已备份到: %BACKUP_PATH%
    ) else (
        echo ✗ 备份失败！
        pause
        exit /b 1
    )
) else (
    echo ✗ 数据库文件不存在: %DB_PATH%
    pause
    exit /b 1
)

echo.
echo 第2步：执行数据迁移
echo -------------------------------------------------------------------------------
cd /d "%SCRIPT_DIR%"
D:\Python3.13.1\python.exe migrate_consolidate_publish_data.py

if %errorlevel% equ 0 (
    echo.
    echo ===============================================================================
    echo ✓ 迁移成功完成！
    echo ===============================================================================
    echo.
    echo 备份文件保存在: %BACKUP_PATH%
    echo 如果需要回滚，可以执行:
    echo   copy "%BACKUP_PATH%" "%DB_PATH%"
    echo.
) else (
    echo.
    echo ===============================================================================
    echo ✗ 迁移失败！
    echo ===============================================================================
    echo.
    echo 数据库已回滚到迁移前的状态
    echo 备份文件: %BACKUP_PATH%
    echo.
)

pause
