#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复服务器应用
"""

import paramiko
import sys
import time

# 服务器信息
SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"
APP_DIR = "/home/u_topn/TOP_N"

def fix_server_app():
    """修复服务器应用"""
    print("=" * 80)
    print("  修复服务器应用")
    print("=" * 80)

    try:
        # 创建SSH客户端
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        print(f"\n正在连接服务器 {SERVER_HOST}...")
        ssh.connect(
            hostname=SERVER_HOST,
            username=SERVER_USER,
            password=SERVER_PASSWORD,
            timeout=30
        )
        print("[OK] 连接成功")

        # 1. 检查8080端口被什么进程占用
        print("\n" + "=" * 80)
        print("1. 检查8080端口占用情况")
        print("=" * 80)
        stdin, stdout, stderr = ssh.exec_command("lsof -i :8080 | grep LISTEN")
        port_process = stdout.read().decode('utf-8', errors='ignore')
        print(port_process if port_process.strip() else "(无进程监听8080)")

        # 2. 杀死所有8080端口进程
        print("\n" + "=" * 80)
        print("2. 停止8080端口所有进程")
        print("=" * 80)
        stdin, stdout, stderr = ssh.exec_command("fuser -k 8080/tcp 2>&1")
        kill_result = stdout.read().decode('utf-8', errors='ignore')
        print(kill_result if kill_result.strip() else "[OK] 没有进程需要停止")
        time.sleep(2)

        # 3. 杀死所有gunicorn进程
        print("\n" + "=" * 80)
        print("3. 停止所有Gunicorn进程")
        print("=" * 80)
        stdin, stdout, stderr = ssh.exec_command("pkill -f gunicorn")
        time.sleep(2)
        print("[OK] Gunicorn进程已清理")

        # 4. 确认端口已释放
        print("\n" + "=" * 80)
        print("4. 确认端口已释放")
        print("=" * 80)
        stdin, stdout, stderr = ssh.exec_command("netstat -tuln | grep 8080")
        port_check = stdout.read().decode('utf-8', errors='ignore')
        if port_check.strip():
            print("[WARN] 端口仍被占用:")
            print(port_check)
        else:
            print("[OK] 端口8080已释放")

        # 5. 检查应用文件
        print("\n" + "=" * 80)
        print("5. 检查应用文件")
        print("=" * 80)
        stdin, stdout, stderr = ssh.exec_command(f"ls -lh {APP_DIR}/backend/app.py")
        file_check = stdout.read().decode('utf-8', errors='ignore')
        print(file_check)

        # 6. 启动应用
        print("\n" + "=" * 80)
        print("6. 启动应用")
        print("=" * 80)

        start_cmd = f"""cd {APP_DIR} && nohup gunicorn -w 4 -b 0.0.0.0:8080 \\
  --access-logfile gunicorn_access.log \\
  --error-logfile gunicorn_error.log \\
  --timeout 120 \\
  backend.app:app > /dev/null 2>&1 &"""

        stdin, stdout, stderr = ssh.exec_command(start_cmd)
        stdout.read()  # 等待命令执行
        time.sleep(3)
        print("[OK] 启动命令已执行")

        # 7. 检查进程状态
        print("\n" + "=" * 80)
        print("7. 检查新进程状态")
        print("=" * 80)
        stdin, stdout, stderr = ssh.exec_command("ps aux | grep 'gunicorn.*app' | grep -v grep")
        process_info = stdout.read().decode('utf-8', errors='ignore')
        if process_info.strip():
            print("[OK] 应用正在运行:")
            print(process_info)
        else:
            print("[FAIL] 应用启动失败")
            # 查看错误日志
            print("\n查看错误日志:")
            stdin, stdout, stderr = ssh.exec_command(f"tail -n 20 {APP_DIR}/gunicorn_error.log")
            error_log = stdout.read().decode('utf-8', errors='ignore')
            print(error_log)

        # 8. 测试API
        print("\n" + "=" * 80)
        print("8. 测试API端点")
        print("=" * 80)
        time.sleep(2)
        stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8080/health")
        health_response = stdout.read().decode('utf-8', errors='ignore')
        print("GET /health:")
        print(health_response)

        ssh.close()
        print("\n" + "=" * 80)
        print("[OK] 修复完成")
        print("=" * 80)
        print("\n请访问: http://39.105.12.124:8080")

    except Exception as e:
        print(f"\n[ERROR] 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = fix_server_app()
    sys.exit(0 if success else 1)
