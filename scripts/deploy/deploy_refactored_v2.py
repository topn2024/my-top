# -*- coding: utf-8 -*-
"""
部署重构后的代码到生产服务器 (使用临时目录)
"""

import paramiko
import os
import sys
from pathlib import Path

# 服务器配置
SERVER_HOST = '39.105.12.124'
SERVER_PORT = 22
SERVER_USER = 'lihanya'
SERVER_PASSWORD = '@WSX2wsx'

# 项目路径
LOCAL_BASE = Path(__file__).parent.parent.parent
REMOTE_TEMP = '/tmp/topn_deploy'
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

def execute_command(ssh, command):
    """执行SSH命令"""
    print(f"Executing: {command}")
    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')

    exit_status = stdout.channel.recv_exit_status()

    if output:
        print(f"Output: {output}")
    if error and exit_status != 0:
        print(f"Error: {error}")

    return output, error, exit_status

def deploy():
    """执行部署"""
    try:
        # 连接服务器
        print("="*60)
        print("Connecting to server...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SERVER_HOST, port=SERVER_PORT,
                   username=SERVER_USER, password=SERVER_PASSWORD)

        sftp = ssh.open_sftp()
        print("Connected successfully!")

        # 1. 创建临时目录
        print("\n" + "="*60)
        print("Step 1: Create temp directory...")
        execute_command(ssh, f"rm -rf {REMOTE_TEMP}")
        execute_command(ssh, f"mkdir -p {REMOTE_TEMP}/backend/services")
        execute_command(ssh, f"mkdir -p {REMOTE_TEMP}/backend/blueprints")
        print("Temp directory created!")

        # 2. 上传文件到临时目录
        print("\n" + "="*60)
        print("Step 2: Upload files to temp...")
        for file_path in FILES_TO_DEPLOY:
            local_file = LOCAL_BASE / file_path
            remote_file = f"{REMOTE_TEMP}/{file_path}"

            if local_file.exists():
                print(f"  Uploading: {file_path}")
                sftp.put(str(local_file), remote_file)
            else:
                print(f"  WARNING: File not found: {file_path}")
        print("Files uploaded to temp!")

        # 3. 使用sudo复制文件到目标目录
        print("\n" + "="*60)
        print("Step 3: Copy files with sudo...")

        # 备份
        backup_cmd = f"echo '{SERVER_PASSWORD}' | sudo -S cp -r {REMOTE_BASE}/backend {REMOTE_BASE}/backend_backup_$(date +%Y%m%d_%H%M%S)"
        execute_command(ssh, backup_cmd)

        # 复制文件
        copy_cmd = f"echo '{SERVER_PASSWORD}' | sudo -S cp -r {REMOTE_TEMP}/backend/* {REMOTE_BASE}/backend/"
        execute_command(ssh, copy_cmd)

        # 复制gunicorn_config.py
        if (LOCAL_BASE / 'gunicorn_config.py').exists():
            copy_config = f"echo '{SERVER_PASSWORD}' | sudo -S cp {REMOTE_TEMP}/gunicorn_config.py {REMOTE_BASE}/"
            execute_command(ssh, copy_config)

        print("Files copied!")

        # 4. 设置权限
        print("\n" + "="*60)
        print("Step 4: Set permissions...")
        chown_cmd = f"echo '{SERVER_PASSWORD}' | sudo -S chown -R u_topn:u_topn {REMOTE_BASE}/backend"
        execute_command(ssh, chown_cmd)
        print("Permissions set!")

        # 5. 验证文件
        print("\n" + "="*60)
        print("Step 5: Verify files...")
        execute_command(ssh, f"echo '{SERVER_PASSWORD}' | sudo -S ls -lh {REMOTE_BASE}/backend/app_factory.py")
        execute_command(ssh, f"echo '{SERVER_PASSWORD}' | sudo -S ls -lh {REMOTE_BASE}/backend/services/")
        execute_command(ssh, f"echo '{SERVER_PASSWORD}' | sudo -S ls -lh {REMOTE_BASE}/backend/blueprints/")
        print("Files verified!")

        # 6. 停止旧服务
        print("\n" + "="*60)
        print("Step 6: Stop old service...")
        stop_cmd = f"echo '{SERVER_PASSWORD}' | sudo -S pkill -9 -f 'gunicorn.*app'"
        execute_command(ssh, stop_cmd)
        import time
        time.sleep(3)
        print("Old service stopped!")

        # 7. 启动新服务
        print("\n" + "="*60)
        print("Step 7: Start new service (app_factory)...")
        start_cmd = (
            f"echo '{SERVER_PASSWORD}' | sudo -S su - u_topn -c '"
            f"cd {REMOTE_BASE}/backend && "
            f"nohup python3.14 -m gunicorn "
            f"--config {REMOTE_BASE}/gunicorn_config.py "
            f"app_factory:app "
            f"> {REMOTE_BASE}/logs/gunicorn.log 2>&1 &'"
        )
        execute_command(ssh, start_cmd)
        time.sleep(5)
        print("New service started!")

        # 8. 验证服务
        print("\n" + "="*60)
        print("Step 8: Verify service...")
        execute_command(ssh, "ps aux | grep 'app_factory' | grep -v grep")
        execute_command(ssh, "netstat -tuln | grep 8080")
        print("Service verified!")

        # 9. 测试API
        print("\n" + "="*60)
        print("Step 9: Test API...")
        execute_command(ssh, "curl -s http://localhost:8080/ | head -20")
        print("API tested!")

        # 10. 查看日志
        print("\n" + "="*60)
        print("Step 10: View logs...")
        execute_command(ssh, f"echo '{SERVER_PASSWORD}' | sudo -S tail -20 {REMOTE_BASE}/logs/gunicorn_error.log")

        # 清理临时目录
        execute_command(ssh, f"rm -rf {REMOTE_TEMP}")

        sftp.close()
        ssh.close()

        print("\n" + "="*60)
        print("SUCCESS: Deployment completed!")
        print("="*60)
        print(f"\nURL: http://39.105.12.124:8080")
        print(f"New Architecture: app_factory + services + blueprints")
        print(f"\nRollback command:")
        print(f"  sudo su - u_topn")
        print(f"  cd {REMOTE_BASE}/backend")
        print(f"  pkill -9 -f gunicorn")
        print(f"  nohup python3.14 -m gunicorn --config {REMOTE_BASE}/gunicorn_config.py app_with_upload:app > {REMOTE_BASE}/logs/gunicorn.log 2>&1 &")

        return True

    except Exception as e:
        print(f"\nERROR: Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*60)
    print("TOP_N Refactored Code Deployment")
    print("="*60)

    success = deploy()
    sys.exit(0 if success else 1)
