# -*- coding: utf-8 -*-
"""
部署重构后的代码到生产服务器 (直接使用u_topn用户)
"""

import paramiko
import os
import sys
from pathlib import Path

# 服务器配置 - 使用u_topn用户
SERVER_HOST = '39.105.12.124'
SERVER_PORT = 22
SERVER_USER = 'u_topn'
SERVER_PASSWORD = '@WSX2wsx'  # 需要u_topn用户的密码

# 项目路径
LOCAL_BASE = Path(__file__).parent.parent.parent
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
]

def execute_command(ssh, command):
    """执行SSH命令"""
    print(f">>> {command}")
    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    exit_status = stdout.channel.recv_exit_status()

    if output.strip():
        print(output)
    if error.strip() and exit_status != 0:
        print(f"[ERROR] {error}")

    return output, error, exit_status

def deploy():
    """执行部署"""
    try:
        # 连接服务器
        print("="*60)
        print("Connecting to u_topn@39.105.12.124...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SERVER_HOST, port=SERVER_PORT,
                   username=SERVER_USER, password=SERVER_PASSWORD)

        sftp = ssh.open_sftp()
        print("Connected!")

        # 1. 备份当前代码
        print("\n" + "="*60)
        print("Step 1: Backup current backend...")
        backup_cmd = f"cd {REMOTE_BASE} && cp -r backend backend_backup_$(date +%Y%m%d_%H%M%S)"
        execute_command(ssh, backup_cmd)

        # 2. 创建目录
        print("\n" + "="*60)
        print("Step 2: Ensure directories exist...")
        execute_command(ssh, f"mkdir -p {REMOTE_BASE}/backend/services")
        execute_command(ssh, f"mkdir -p {REMOTE_BASE}/backend/blueprints")

        # 3. 上传文件
        print("\n" + "="*60)
        print("Step 3: Upload refactored files...")
        for file_path in FILES_TO_DEPLOY:
            local_file = LOCAL_BASE / file_path
            remote_file = f"{REMOTE_BASE}/{file_path}"

            if local_file.exists():
                print(f"  {file_path}")
                sftp.put(str(local_file), remote_file)
            else:
                print(f"  [SKIP] {file_path} (not found)")

        # 上传gunicorn_config.py (如果存在)
        if (LOCAL_BASE / 'gunicorn_config.py').exists():
            print(f"  gunicorn_config.py")
            sftp.put(str(LOCAL_BASE / 'gunicorn_config.py'), f"{REMOTE_BASE}/gunicorn_config.py")

        print("Upload completed!")

        # 4. 验证文件
        print("\n" + "="*60)
        print("Step 4: Verify files...")
        execute_command(ssh, f"ls -lh {REMOTE_BASE}/backend/app_factory.py")
        execute_command(ssh, f"ls -lh {REMOTE_BASE}/backend/services/ | head -10")
        execute_command(ssh, f"ls -lh {REMOTE_BASE}/backend/blueprints/ | head -10")

        # 5. 检查当前服务
        print("\n" + "="*60)
        print("Step 5: Check current service...")
        execute_command(ssh, "ps aux | grep '[g]unicorn.*app'")

        # 6. 停止旧服务
        print("\n" + "="*60)
        print("Step 6: Stop old service...")
        execute_command(ssh, "pkill -9 -f 'gunicorn.*app'")

        import time
        time.sleep(3)
        print("Service stopped!")

        # 7. 启动新服务 (app_factory)
        print("\n" + "="*60)
        print("Step 7: Start new service with app_factory...")

        start_cmd = (
            f"cd {REMOTE_BASE}/backend && "
            f"nohup python3.14 -m gunicorn "
            f"--config {REMOTE_BASE}/gunicorn_config.py "
            f"app_factory:app "
            f"> {REMOTE_BASE}/logs/gunicorn.log 2>&1 &"
        )
        execute_command(ssh, start_cmd)

        time.sleep(5)
        print("Service started!")

        # 8. 验证新服务
        print("\n" + "="*60)
        print("Step 8: Verify new service...")
        execute_command(ssh, "ps aux | grep '[a]pp_factory'")
        execute_command(ssh, "netstat -tuln | grep 8080")

        # 9. 测试API
        print("\n" + "="*60)
        print("Step 9: Test API endpoint...")
        execute_command(ssh, "curl -s http://localhost:8080/ | head -10")

        # 10. 查看日志
        print("\n" + "="*60)
        print("Step 10: Check logs...")
        execute_command(ssh, f"tail -30 {REMOTE_BASE}/logs/gunicorn_error.log")

        sftp.close()
        ssh.close()

        print("\n" + "="*60)
        print("DEPLOYMENT SUCCESSFUL!")
        print("="*60)
        print(f"\nService URL: http://39.105.12.124:8080")
        print(f"Architecture: app_factory + services + blueprints")
        print(f"\nTo rollback:")
        print(f"  ssh u_topn@39.105.12.124")
        print(f"  pkill -9 -f gunicorn")
        print(f"  cd {REMOTE_BASE}/backend")
        print(f"  nohup python3.14 -m gunicorn --config {REMOTE_BASE}/gunicorn_config.py app_with_upload:app > {REMOTE_BASE}/logs/gunicorn.log 2>&1 &")

        return True

    except Exception as e:
        print(f"\nDEPLOYMENT FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*60)
    print("TOP_N Refactored Code Deployment")
    print("Using u_topn user for direct deployment")
    print("="*60)

    success = deploy()
    sys.exit(0 if success else 1)
