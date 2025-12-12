#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步代码并部署到服务器
将重构后的代码完整同步到服务器,并重启服务
"""

import paramiko
import os
import sys
import time
import io
from pathlib import Path

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 服务器配置
SERVER = "39.105.12.124"
USER = "u_topn"
PASSWORD = "TopN@2024"
DEPLOY_DIR = "/home/u_topn/TOP_N"
BACKUP_DIR = "/home/u_topn/backup"

# 本地项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def print_header(text):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")

def print_step(step_num, text):
    """打印步骤"""
    print(f"\n【步骤 {step_num}】{text}")
    print("-" * 60)

def execute_command(ssh, command, use_sudo=False, timeout=60, show_output=True):
    """执行 SSH 命令"""
    if use_sudo:
        command = f"echo {PASSWORD} | sudo -S {command}"

    if show_output:
        print(f"执行: {command}")

    stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)

    # 读取输出
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    exit_code = stdout.channel.recv_exit_status()

    if show_output and output:
        print(output)
    if error and "sudo" not in error.lower() and "password for" not in error.lower():
        if show_output:
            print(f"stderr: {error}")

    return exit_code, output, error

def connect_to_server():
    """连接到服务器"""
    print_step(1, "连接到服务器")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=10)
        print(f"✓ 成功连接到 {SERVER}")
        return ssh
    except Exception as e:
        print(f"✗ 连接失败: {e}")
        sys.exit(1)

def backup_current_code(ssh):
    """备份服务器上的当前代码"""
    print_step(2, "备份服务器上的当前代码")

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_path = f"{BACKUP_DIR}/TOP_N_backup_{timestamp}"

    commands = [
        f"mkdir -p {BACKUP_DIR}",
        f"if [ -d {DEPLOY_DIR} ]; then cp -r {DEPLOY_DIR} {backup_path}; echo '✓ 备份完成: {backup_path}'; else echo '✓ 无需备份,目录不存在'; fi",
        f"ls -lh {BACKUP_DIR} | tail -5"
    ]

    for cmd in commands:
        execute_command(ssh, cmd)

def check_server_status(ssh):
    """检查服务器当前状态"""
    print_step(3, "检查服务器当前状态")

    commands = [
        ("Python版本", "python3 --version 2>&1"),
        ("当前运行的服务", "ps aux | grep -E 'gunicorn|app_factory|app_with_upload' | grep -v grep"),
        ("服务端口占用", "netstat -tlnp 2>/dev/null | grep -E ':3001|:8080' || ss -tlnp | grep -E ':3001|:8080'"),
        ("磁盘空间", "df -h | grep -E 'Filesystem|/$'"),
        ("项目目录", f"ls -lh {DEPLOY_DIR} 2>/dev/null || echo '目录不存在'"),
    ]

    for name, cmd in commands:
        print(f"\n{name}:")
        execute_command(ssh, cmd)

def stop_services(ssh):
    """停止当前运行的服务"""
    print_step(4, "停止当前运行的服务")

    # 尝试多种方式停止服务
    commands = [
        # 停止 systemd 服务
        "systemctl stop topn 2>/dev/null || true",
        # 杀死 gunicorn 进程
        "pkill -f gunicorn || true",
        # 杀死 Python 应用进程
        "pkill -f 'app_factory|app_with_upload' || true",
        # 等待进程退出
        "sleep 2",
        # 确认进程已停止
        "ps aux | grep -E 'gunicorn|app_factory|app_with_upload' | grep -v grep || echo '✓ 所有服务已停止'"
    ]

    for cmd in commands:
        execute_command(ssh, cmd, use_sudo=True)

def upload_files(ssh):
    """上传重构后的代码到服务器"""
    print_step(5, "上传重构后的代码到服务器")

    sftp = ssh.open_sftp()

    # 需要上传的目录和文件
    directories_to_sync = [
        "backend",
        "templates",
        "static",
        "scripts",
        "docs"
    ]

    files_to_sync = [
        "requirements.txt",
        "requirements_new.txt",
        "start.sh",
        "README.md",
        "DIRECTORY_STANDARD.md"
    ]

    # 创建远程目录
    print(f"创建远程目录: {DEPLOY_DIR}")
    execute_command(ssh, f"mkdir -p {DEPLOY_DIR}")

    # 上传目录
    for dir_name in directories_to_sync:
        local_dir = PROJECT_ROOT / dir_name
        if not local_dir.exists():
            print(f"⚠ 跳过不存在的目录: {dir_name}")
            continue

        print(f"\n上传目录: {dir_name}")
        remote_dir = f"{DEPLOY_DIR}/{dir_name}"

        # 创建远程目录
        execute_command(ssh, f"mkdir -p {remote_dir}", show_output=False)

        # 递归上传文件
        upload_directory(sftp, ssh, local_dir, remote_dir)

    # 上传文件
    print("\n上传配置文件:")
    for file_name in files_to_sync:
        local_file = PROJECT_ROOT / file_name
        if not local_file.exists():
            print(f"⚠ 跳过不存在的文件: {file_name}")
            continue

        remote_file = f"{DEPLOY_DIR}/{file_name}"
        print(f"  {file_name}")
        sftp.put(str(local_file), remote_file)

    # 创建必要的目录
    print("\n创建必要的目录:")
    necessary_dirs = ["data", "uploads", "logs", "accounts", "backend/cookies"]
    for dir_name in necessary_dirs:
        remote_dir = f"{DEPLOY_DIR}/{dir_name}"
        execute_command(ssh, f"mkdir -p {remote_dir}", show_output=False)
        print(f"  ✓ {dir_name}")

    sftp.close()
    print("\n✓ 代码上传完成")

def upload_directory(sftp, ssh, local_dir, remote_dir):
    """递归上传目录"""
    for item in local_dir.iterdir():
        local_path = item
        remote_path = f"{remote_dir}/{item.name}"

        # 跳过特定目录和文件
        skip_patterns = [
            '__pycache__', '.pyc', '.git', '.gitignore',
            'node_modules', '.env', 'venv', '.venv',
            '.DS_Store', 'Thumbs.db', '*.log'
        ]

        if any(pattern in item.name for pattern in skip_patterns):
            continue

        try:
            if item.is_file():
                # 上传文件
                sftp.put(str(local_path), remote_path)
            elif item.is_dir():
                # 创建远程目录并递归上传
                try:
                    sftp.stat(remote_path)
                except:
                    execute_command(ssh, f"mkdir -p {remote_path}", show_output=False)
                upload_directory(sftp, ssh, local_path, remote_path)
        except Exception as e:
            print(f"⚠ 上传失败 {item.name}: {e}")

def setup_environment(ssh):
    """设置服务器环境"""
    print_step(6, "设置服务器环境")

    commands = [
        # 设置正确的权限
        f"chmod +x {DEPLOY_DIR}/start.sh",
        f"chmod -R 755 {DEPLOY_DIR}/backend",
        f"chmod -R 755 {DEPLOY_DIR}/scripts",
        # 检查 Python 包
        "python3 -m pip list | grep -E 'Flask|SQLAlchemy|gunicorn' || echo '需要安装依赖包'",
    ]

    for cmd in commands:
        execute_command(ssh, cmd)

    # 检查是否需要安装依赖
    print("\n检查 Python 依赖...")
    code, output, _ = execute_command(ssh, f"cd {DEPLOY_DIR} && python3 -c 'import flask, sqlalchemy, gunicorn' 2>&1", show_output=False)

    if code != 0:
        print("⚠ 需要安装依赖包")
        print("安装 Python 依赖...")
        execute_command(ssh, f"cd {DEPLOY_DIR} && python3 -m pip install -r requirements.txt --user", timeout=120)
    else:
        print("✓ Python 依赖已满足")

def check_database(ssh):
    """检查数据库状态"""
    print_step(7, "检查数据库状态")

    # 检查 MySQL 服务
    print("检查 MySQL 服务...")
    code, output, _ = execute_command(ssh, "systemctl status mysql 2>&1 | head -5", use_sudo=True)

    if "active (running)" in output.lower():
        print("✓ MySQL 服务正在运行")
    else:
        print("⚠ MySQL 服务未运行")

    # 测试数据库连接
    print("\n测试数据库连接...")
    test_cmd = f"""cd {DEPLOY_DIR}/backend && python3 -c "
from models import engine
try:
    conn = engine.connect()
    print('✓ 数据库连接成功')
    conn.close()
except Exception as e:
    print(f'✗ 数据库连接失败: {{e}}')
" 2>&1"""

    execute_command(ssh, test_cmd)

def start_service(ssh):
    """启动服务"""
    print_step(8, "启动服务")

    # 使用 gunicorn 启动服务
    start_cmd = f"""cd {DEPLOY_DIR} && nohup gunicorn -c backend/gunicorn_config.py 'backend.app_factory:app' > logs/gunicorn.log 2>&1 &"""

    # 检查是否有 gunicorn 配置文件
    code, _, _ = execute_command(ssh, f"test -f {DEPLOY_DIR}/backend/gunicorn_config.py && echo 'exists' || echo 'not exists'", show_output=False)

    if code != 0:
        # 没有配置文件,使用默认参数
        print("使用默认 gunicorn 配置启动服务...")
        start_cmd = f"""cd {DEPLOY_DIR} && nohup gunicorn -w 4 -b 0.0.0.0:3001 --timeout 120 'backend.app_factory:app' > logs/gunicorn.log 2>&1 &"""

    execute_command(ssh, start_cmd)

    print("\n等待服务启动...")
    time.sleep(3)

    # 检查服务状态
    print("\n检查服务状态:")
    execute_command(ssh, "ps aux | grep gunicorn | grep -v grep")

def test_service(ssh):
    """测试服务基本功能"""
    print_step(9, "测试服务基本功能")

    # 等待服务完全启动
    print("等待服务完全启动...")
    time.sleep(2)

    # 测试健康检查端点
    print("\n1. 测试健康检查端点:")
    execute_command(ssh, "curl -s http://localhost:3001/api/health | python3 -m json.tool || curl -s http://localhost:3001/api/health")

    # 测试首页
    print("\n2. 测试首页访问:")
    code, output, _ = execute_command(ssh, "curl -s -o /dev/null -w '%{http_code}' http://localhost:3001/")
    if "200" in output:
        print("✓ 首页访问正常 (HTTP 200)")
    else:
        print(f"⚠ 首页访问异常 (HTTP {output})")

    # 检查日志
    print("\n3. 查看最新日志:")
    execute_command(ssh, f"tail -20 {DEPLOY_DIR}/logs/gunicorn.log 2>/dev/null || tail -20 {DEPLOY_DIR}/logs/gunicorn_error.log 2>/dev/null || echo '无日志文件'")

    # 测试外部访问
    print("\n4. 外部访问测试:")
    print(f"   请在浏览器访问: http://{SERVER}:3001")
    print(f"   健康检查: http://{SERVER}:3001/api/health")

def show_summary(ssh):
    """显示部署摘要"""
    print_header("部署摘要")

    print("服务器信息:")
    print(f"  地址: {SERVER}")
    print(f"  用户: {USER}")
    print(f"  目录: {DEPLOY_DIR}")

    print("\n服务状态:")
    code, output, _ = execute_command(ssh, "ps aux | grep gunicorn | grep -v grep | wc -l", show_output=False)
    process_count = output.strip()
    if int(process_count) > 0:
        print(f"  ✓ Gunicorn 进程数: {process_count}")
    else:
        print(f"  ✗ 未检测到运行的进程")

    print("\n端口监听:")
    execute_command(ssh, "netstat -tlnp 2>/dev/null | grep :3001 || ss -tlnp | grep :3001 || echo '未检测到3001端口监听'")

    print("\n访问地址:")
    print(f"  主页: http://{SERVER}:3001")
    print(f"  API: http://{SERVER}:3001/api/health")

    print("\n常用命令:")
    print(f"  查看日志: tail -f {DEPLOY_DIR}/logs/gunicorn.log")
    print(f"  重启服务: pkill -f gunicorn && cd {DEPLOY_DIR} && gunicorn -w 4 -b 0.0.0.0:3001 'backend.app_factory:app'")
    print(f"  停止服务: pkill -f gunicorn")

def main():
    """主函数"""
    print_header("TOP_N 代码同步与部署")

    print(f"本地项目目录: {PROJECT_ROOT}")
    print(f"服务器地址: {SERVER}")
    print(f"部署目录: {DEPLOY_DIR}")

    # 检查是否有命令行参数 --auto-confirm
    auto_confirm = '--auto-confirm' in sys.argv or '-y' in sys.argv

    if not auto_confirm:
        # 确认操作
        try:
            confirm = input("\n确认开始部署? (yes/no): ")
            if confirm.lower() not in ['yes', 'y']:
                print("部署已取消")
                sys.exit(0)
        except (EOFError, KeyboardInterrupt):
            print("\n部署已取消")
            sys.exit(0)
    else:
        print("\n自动确认模式,开始部署...")

    try:
        # 连接服务器
        ssh = connect_to_server()

        # 备份当前代码
        backup_current_code(ssh)

        # 检查服务器状态
        check_server_status(ssh)

        # 停止服务
        stop_services(ssh)

        # 上传文件
        upload_files(ssh)

        # 设置环境
        setup_environment(ssh)

        # 检查数据库
        check_database(ssh)

        # 启动服务
        start_service(ssh)

        # 测试服务
        test_service(ssh)

        # 显示摘要
        show_summary(ssh)

        print_header("部署完成!")
        print("✓ 代码同步成功")
        print("✓ 服务已启动")
        print("\n请测试基本功能确认一切正常")

    except Exception as e:
        print(f"\n✗ 部署失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if 'ssh' in locals():
            ssh.close()

if __name__ == '__main__':
    main()
