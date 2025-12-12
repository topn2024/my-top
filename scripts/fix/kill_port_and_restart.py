#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
杀死占用端口的进程并重启服务
"""

import paramiko
import sys
import io
import time

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 服务器配置
SERVER = "39.105.12.124"
USER = "u_topn"
PASSWORD = "TopN@2024"
DEPLOY_DIR = "/home/u_topn/TOP_N"

def execute(ssh, cmd, show=True, use_sudo=False):
    if use_sudo:
        cmd = f"echo {PASSWORD} | sudo -S {cmd}"
    if show:
        print(f"\n执行: {cmd if not use_sudo else cmd.replace(PASSWORD, '***')}")
        print("-" * 60)
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    if show and output:
        print(output)
    if show and error and "sudo" not in error.lower() and "password for" not in error.lower():
        print(f"stderr: {error}")
    return output, error

def main():
    print("=" * 60)
    print("  杀死占用端口的进程并重启服务")
    print("=" * 60)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=10)
        print("✓ 已连接到服务器\n")

        # 1. 查找占用3001端口的进程
        print("【1】查找占用 3001 端口的进程")
        out, _ = execute(ssh, "lsof -i :3001 || fuser 3001/tcp || netstat -tlnp | grep :3001 | awk '{print $7}' | cut -d/ -f1")

        # 2. 杀死所有相关进程
        print("\n【2】杀死所有相关进程")
        execute(ssh, "pkill -9 -f gunicorn || true")
        execute(ssh, "pkill -9 -f 'app_factory|app_with_upload' || true")
        execute(ssh, "fuser -k 3001/tcp 2>/dev/null || true", use_sudo=True)
        execute(ssh, "sleep 2")

        # 3. 确认端口已释放
        print("\n【3】确认端口已释放")
        execute(ssh, "netstat -tlnp | grep :3001 || echo '✓ 端口3001已释放'")

        # 4. 确认无残留进程
        print("\n【4】确认无残留进程")
        execute(ssh, "ps aux | grep -E 'gunicorn|app_factory' | grep -v grep || echo '✓ 无残留进程'")

        # 5. 清理旧日志
        print("\n【5】清理旧日志")
        execute(ssh, f"rm -f {DEPLOY_DIR}/logs/*.log", show=False)
        execute(ssh, f"echo '✓ 日志已清理'")

        # 6. 启动新服务
        print("\n【6】启动新服务")
        start_cmd = f"""cd {DEPLOY_DIR} && nohup python3 -m gunicorn \\
            -w 4 \\
            -b 0.0.0.0:3001 \\
            --timeout 120 \\
            --access-logfile logs/access.log \\
            --error-logfile logs/error.log \\
            'backend.app_factory:app' \\
            > logs/startup.log 2>&1 &"""

        execute(ssh, start_cmd)

        # 7. 等待启动
        print("\n【7】等待服务启动...")
        for i in range(5):
            time.sleep(1)
            out, _ = execute(ssh, "ps aux | grep gunicorn | grep -v grep | wc -l", show=False)
            if int(out.strip()) > 0:
                print(f"✓ 服务已启动 (进程数: {out.strip()})")
                break
            print(f"  等待中... ({i+1}/5)")
        else:
            print("⚠ 服务可能未正常启动")

        # 8. 检查进程
        print("\n【8】检查进程状态")
        execute(ssh, "ps aux | grep gunicorn | grep -v grep")

        # 9. 检查端口
        print("\n【9】检查端口监听")
        execute(ssh, "netstat -tlnp | grep :3001 || ss -tlnp | grep :3001")

        # 10. 测试访问
        print("\n【10】测试 HTTP 访问")
        time.sleep(2)  # 等待应用完全启动

        execute(ssh, "curl -s http://localhost:3001/api/health | head -3")

        out, _ = execute(ssh, "curl -s -o /dev/null -w '%{http_code}' http://localhost:3001/", show=False)
        status_code = out.strip()
        print(f"\n首页状态码: {status_code}")

        if "200" in status_code:
            print("✓ 首页访问正常!")
        else:
            print(f"⚠ 首页返回 {status_code},查看错误日志:")
            execute(ssh, f"tail -30 {DEPLOY_DIR}/logs/error.log")
            execute(ssh, f"tail -30 {DEPLOY_DIR}/logs/startup.log")

        # 11. 外部访问提示
        print("\n" + "=" * 60)
        print("  部署完成!")
        print("=" * 60)
        print(f"\n外部访问地址:")
        print(f"  主页: http://{SERVER}:3001")
        print(f"  API: http://{SERVER}:3001/api/health")

    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == '__main__':
    main()
