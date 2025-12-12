#!/usr/bin/env python3
"""
部署重构后的代码到生产服务器
"""

import paramiko
import os
import sys
from pathlib import Path

# 服务器配置
SERVER_CONFIG = {
    'host': '39.105.12.124',
    'port': 22,
    'username': 'lihanya',
    'password': '@WSX2wsx'
}

# 项目路径
LOCAL_BASE = Path(__file__).parent.parent.parent  # TOP_N根目录
REMOTE_BASE = '/home/u_topn/TOP_N'

# 需要部署的文件
FILES_TO_DEPLOY = [
    'backend/config.py',
    'backend/app_factory.py',
    'backend/services/__init__.py',
    'backend/services/file_service.py',
    'backend/services/ai_service.py',
    'backend/services/account_service.py',
    'backend/services/workflow_service.py',
    'backend/services/publish_service.py',
    'backend/blueprints/__init__.py',
    'backend/blueprints/api.py',
    'backend/blueprints/auth.py',
    'backend/blueprints/pages.py',
    'gunicorn_config.py'
]

def execute_ssh_command(ssh, command):
    """执行SSH命令"""
    print(f"执行: {command}")
    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')

    if output:
        print(f"输出: {output}")
    if error:
        print(f"错误: {error}")

    return output, error, stdout.channel.recv_exit_status()

def deploy():
    """执行部署"""
    try:
        # 连接服务器
        print("=" * 60)
        print("连接服务器...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(**SERVER_CONFIG)

        sftp = ssh.open_sftp()
        print("✅ 连接成功")

        # 1. 备份当前代码
        print("\n" + "=" * 60)
        print("步骤 1: 备份当前代码...")
        backup_cmd = f"cd {REMOTE_BASE} && cp -r backend backend_backup_$(date +%Y%m%d_%H%M%S)"
        execute_ssh_command(ssh, backup_cmd)
        print("✅ 备份完成")

        # 2. 确保目录存在
        print("\n" + "=" * 60)
        print("步骤 2: 创建目录结构...")
        dirs_to_create = [
            f"{REMOTE_BASE}/backend/services",
            f"{REMOTE_BASE}/backend/blueprints"
        ]
        for dir_path in dirs_to_create:
            execute_ssh_command(ssh, f"mkdir -p {dir_path}")
        print("✅ 目录创建完成")

        # 3. 上传文件
        print("\n" + "=" * 60)
        print("步骤 3: 上传重构后的代码...")
        for file_path in FILES_TO_DEPLOY:
            local_file = LOCAL_BASE / file_path
            remote_file = f"{REMOTE_BASE}/{file_path}"

            if local_file.exists():
                print(f"  上传: {file_path}")
                sftp.put(str(local_file), remote_file)
            else:
                print(f"  ⚠️  文件不存在: {file_path}")
        print("✅ 文件上传完成")

        # 4. 验证文件
        print("\n" + "=" * 60)
        print("步骤 4: 验证文件...")
        output, _, _ = execute_ssh_command(ssh, f"ls -lh {REMOTE_BASE}/backend/app_factory.py")
        output, _, _ = execute_ssh_command(ssh, f"ls -lh {REMOTE_BASE}/backend/services/")
        output, _, _ = execute_ssh_command(ssh, f"ls -lh {REMOTE_BASE}/backend/blueprints/")
        print("✅ 文件验证完成")

        # 5. 检查当前运行的服务
        print("\n" + "=" * 60)
        print("步骤 5: 检查当前服务...")
        output, _, _ = execute_ssh_command(ssh, "ps aux | grep gunicorn | grep -v grep")
        print("✅ 服务检查完成")

        # 6. 停止旧服务
        print("\n" + "=" * 60)
        print("步骤 6: 停止旧服务...")
        execute_ssh_command(ssh, "pkill -9 -f 'gunicorn.*app'")
        print("⏱️  等待3秒...")
        import time
        time.sleep(3)
        print("✅ 旧服务已停止")

        # 7. 启动新服务
        print("\n" + "=" * 60)
        print("步骤 7: 启动新服务 (使用 app_factory)...")
        start_cmd = (
            f"cd {REMOTE_BASE}/backend && "
            f"nohup python3.14 -m gunicorn "
            f"--config {REMOTE_BASE}/gunicorn_config.py "
            f"app_factory:app "
            f"> {REMOTE_BASE}/logs/gunicorn.log 2>&1 &"
        )
        execute_ssh_command(ssh, start_cmd)
        print("⏱️  等待5秒让服务启动...")
        time.sleep(5)
        print("✅ 新服务已启动")

        # 8. 验证服务
        print("\n" + "=" * 60)
        print("步骤 8: 验证服务状态...")
        output, _, _ = execute_ssh_command(ssh, "ps aux | grep 'app_factory' | grep -v grep")
        output, _, _ = execute_ssh_command(ssh, "netstat -tuln | grep 8080")
        print("✅ 服务验证完成")

        # 9. 测试API
        print("\n" + "=" * 60)
        print("步骤 9: 测试API...")
        test_cmd = "curl -s http://localhost:8080/ | head -20"
        output, _, _ = execute_ssh_command(ssh, test_cmd)
        print("✅ API测试完成")

        # 10. 查看日志
        print("\n" + "=" * 60)
        print("步骤 10: 查看最新日志...")
        execute_ssh_command(ssh, f"tail -20 {REMOTE_BASE}/logs/gunicorn_error.log")

        # 关闭连接
        sftp.close()
        ssh.close()

        print("\n" + "=" * 60)
        print("✅ 部署成功完成!")
        print("=" * 60)
        print(f"\n访问地址: http://39.105.12.124:8080")
        print(f"新架构: app_factory + services + blueprints")
        print(f"\n回滚方法:")
        print(f"  ssh lihanya@39.105.12.124")
        print(f"  pkill -9 -f 'gunicorn.*app_factory'")
        print(f"  cd {REMOTE_BASE}/backend")
        print(f"  nohup python3.14 -m gunicorn --config {REMOTE_BASE}/gunicorn_config.py app_with_upload:app > {REMOTE_BASE}/logs/gunicorn.log 2>&1 &")

        return True

    except Exception as e:
        print(f"\n❌ 部署失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("TOP_N 重构代码部署脚本")
    print("=" * 60)

    # 检查paramiko是否已安装
    try:
        import paramiko
    except ImportError:
        print("❌ 缺少 paramiko 模块")
        print("安装命令: pip install paramiko")
        sys.exit(1)

    success = deploy()
    sys.exit(0 if success else 1)
