# -*- coding: utf-8 -*-
"""
部署重构后的代码到生产服务器
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
    print("Executing:", command)
    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')

    if output:
        print("Output:", output)
    if error:
        print("Error:", error)

    return output, error

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

        # 1. 备份当前代码
        print("\n" + "="*60)
        print("Step 1: Backup current code...")
        backup_cmd = f"cd {REMOTE_BASE} && cp -r backend backend_backup_$(date +%Y%m%d_%H%M%S)"
        execute_command(ssh, backup_cmd)
        print("Backup completed!")

        # 2. 创建目录
        print("\n" + "="*60)
        print("Step 2: Create directories...")
        dirs = [
            f"{REMOTE_BASE}/backend/services",
            f"{REMOTE_BASE}/backend/blueprints"
        ]
        for d in dirs:
            execute_command(ssh, f"mkdir -p {d}")
        print("Directories created!")

        # 3. 上传文件
        print("\n" + "="*60)
        print("Step 3: Upload files...")
        for file_path in FILES_TO_DEPLOY:
            local_file = LOCAL_BASE / file_path
            remote_file = f"{REMOTE_BASE}/{file_path}"

            if local_file.exists():
                print(f"  Uploading: {file_path}")
                sftp.put(str(local_file), remote_file)
            else:
                print(f"  WARNING: File not found: {file_path}")
        print("Files uploaded!")

        # 4. 验证文件
        print("\n" + "="*60)
        print("Step 4: Verify files...")
        execute_command(ssh, f"ls -lh {REMOTE_BASE}/backend/app_factory.py")
        execute_command(ssh, f"ls -lh {REMOTE_BASE}/backend/services/")
        execute_command(ssh, f"ls -lh {REMOTE_BASE}/backend/blueprints/")
        print("Files verified!")

        # 5. 停止旧服务
        print("\n" + "="*60)
        print("Step 5: Stop old service...")
        execute_command(ssh, "pkill -9 -f 'gunicorn.*app'")
        import time
        time.sleep(3)
        print("Old service stopped!")

        # 6. 启动新服务
        print("\n" + "="*60)
        print("Step 6: Start new service...")
        start_cmd = (
            f"cd {REMOTE_BASE}/backend && "
            f"nohup python3.14 -m gunicorn "
            f"--config {REMOTE_BASE}/gunicorn_config.py "
            f"app_factory:app "
            f"> {REMOTE_BASE}/logs/gunicorn.log 2>&1 &"
        )
        execute_command(ssh, start_cmd)
        time.sleep(5)
        print("New service started!")

        # 7. 验证服务
        print("\n" + "="*60)
        print("Step 7: Verify service...")
        execute_command(ssh, "ps aux | grep 'app_factory' | grep -v grep")
        execute_command(ssh, "netstat -tuln | grep 8080")
        print("Service verified!")

        # 8. 测试API
        print("\n" + "="*60)
        print("Step 8: Test API...")
        execute_command(ssh, "curl -s http://localhost:8080/ | head -20")
        print("API tested!")

        # 9. 查看日志
        print("\n" + "="*60)
        print("Step 9: View logs...")
        execute_command(ssh, f"tail -20 {REMOTE_BASE}/logs/gunicorn_error.log")

        sftp.close()
        ssh.close()

        print("\n" + "="*60)
        print("Deployment completed successfully!")
        print("="*60)
        print(f"\nURL: http://39.105.12.124:8080")
        print(f"Architecture: app_factory + services + blueprints")

        return True

    except Exception as e:
        print(f"\nDeployment failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*60)
    print("TOP_N Refactored Code Deployment")
    print("="*60)

    success = deploy()
    sys.exit(0 if success else 1)
