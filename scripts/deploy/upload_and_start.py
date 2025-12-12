#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上传启动脚本并执行
"""

import paramiko
import sys
import io
import time
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

# 本地文件
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
START_SCRIPT = PROJECT_ROOT / "start_service.sh"

def main():
    print("=" * 60)
    print("  上传并执行启动脚本")
    print("=" * 60)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=10)
        print("✓ 已连接到服务器\n")

        # 1. 上传启动脚本
        print("【1】上传启动脚本")
        sftp = ssh.open_sftp()
        remote_script = f"{DEPLOY_DIR}/start_service.sh"
        sftp.put(str(START_SCRIPT), remote_script)
        sftp.close()
        print(f"✓ 已上传: {remote_script}")

        # 2. 设置执行权限
        print("\n【2】设置执行权限")
        stdin, stdout, stderr = ssh.exec_command(f"chmod +x {remote_script}")
        stdout.read()
        print("✓ 权限已设置")

        # 3. 执行启动脚本
        print("\n【3】执行启动脚本")
        stdin, stdout, stderr = ssh.exec_command(f"bash {remote_script}", timeout=15)
        output = stdout.read().decode('utf-8', errors='ignore')
        print(output)

        # 4. 等待服务完全启动
        print("\n【4】等待服务完全启动...")
        time.sleep(3)

        # 5. 测试访问
        print("\n【5】测试访问")

        # 健康检查
        stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:3001/api/health")
        out = stdout.read().decode('utf-8', errors='ignore')
        print(f"API健康检查: {out.strip()[:100]}")

        # 首页
        stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:3001/")
        status = stdout.read().decode('utf-8', errors='ignore').strip()
        print(f"首页状态码: {status}")

        if "200" in status:
            print("\n✓ 服务启动成功!")
        else:
            print(f"\n⚠ 首页返回 {status},查看日志:")
            stdin, stdout, stderr = ssh.exec_command(f"tail -20 {DEPLOY_DIR}/logs/error.log")
            print(stdout.read().decode('utf-8', errors='ignore'))

        # 6. 测试多个端点
        print("\n【6】测试多个端点")
        endpoints = {
            "/": "首页",
            "/login": "登录页",
            "/platform": "平台页",
            "/api/health": "健康检查"
        }

        for endpoint, name in endpoints.items():
            stdin, stdout, stderr = ssh.exec_command(
                f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:3001{endpoint}"
            )
            code = stdout.read().decode('utf-8', errors='ignore').strip()
            icon = "✓" if code in ["200", "302"] else "✗"
            print(f"  {icon} {name} ({endpoint}): HTTP {code}")

        # 7. 完成信息
        print("\n" + "=" * 60)
        print("  部署完成!")
        print("=" * 60)
        print(f"\n外部访问地址:")
        print(f"  http://{SERVER}:3001")
        print(f"\n常用命令:")
        print(f"  重启: ssh {USER}@{SERVER} 'bash {DEPLOY_DIR}/start_service.sh'")
        print(f"  停止: ssh {USER}@{SERVER} 'pkill -f gunicorn'")
        print(f"  日志: ssh {USER}@{SERVER} 'tail -f {DEPLOY_DIR}/logs/error.log'")

    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == '__main__':
    main()
