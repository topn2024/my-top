#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终修复并启动服务
解决 PYTHONPATH 问题
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

def execute(ssh, cmd, show=True):
    if show:
        print(f"\n执行: {cmd[:100]}...")
        print("-" * 60)
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    if show and output:
        print(output)
    if show and error and "sudo" not in error.lower():
        if "password for" not in error.lower():
            print(f"stderr: {error}")
    return output, error

def main():
    print("=" * 60)
    print("  最终修复并启动服务")
    print("=" * 60)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=10)
        print("✓ 已连接到服务器\n")

        # 1. 停止所有服务
        print("【1】停止所有服务")
        execute(ssh, "pkill -9 -f gunicorn 2>/dev/null || true", show=False)
        execute(ssh, f"echo {PASSWORD} | sudo -S fuser -k 3001/tcp 2>/dev/null || true", show=False)
        execute(ssh, "sleep 2", show=False)
        print("✓ 服务已停止")

        # 2. 启动服务 - 设置正确的 PYTHONPATH
        print("\n【2】启动服务(设置PYTHONPATH)")

        # 方式1: 添加 backend 到 PYTHONPATH
        start_cmd = f"""cd {DEPLOY_DIR} && \\
PYTHONPATH={DEPLOY_DIR}/backend:{DEPLOY_DIR}:$PYTHONPATH \\
nohup python3 -m gunicorn \\
  -w 4 \\
  -b 0.0.0.0:3001 \\
  --timeout 120 \\
  --access-logfile logs/access.log \\
  --error-logfile logs/error.log \\
  'backend.app_factory:app' \\
  > logs/startup.log 2>&1 &"""

        execute(ssh, start_cmd)
        print("✓ 启动命令已执行")

        # 3. 等待启动
        print("\n【3】等待服务启动...")
        for i in range(8):
            time.sleep(1)
            out, _ = execute(ssh, "ps aux | grep gunicorn | grep -v grep | wc -l", show=False)
            count = out.strip()
            if int(count) > 0:
                print(f"✓ 服务已启动 (worker进程数: {count})")
                break
            print(f"  等待中... ({i+1}/8)")
        else:
            print("⚠ 服务可能未正常启动,查看错误日志:")
            execute(ssh, f"tail -20 {DEPLOY_DIR}/logs/error.log")
            execute(ssh, f"tail -20 {DEPLOY_DIR}/logs/startup.log")
            return

        # 4. 检查进程
        print("\n【4】检查进程状态")
        execute(ssh, "ps aux | grep gunicorn | grep -v grep | head -6")

        # 5. 检查端口
        print("\n【5】检查端口监听")
        out, _ = execute(ssh, "netstat -tlnp 2>/dev/null | grep :3001 || ss -tlnp | grep :3001")
        if ":3001" in out:
            print("✓ 端口 3001 正在监听")

        # 6. 测试访问
        print("\n【6】测试 HTTP 访问")
        time.sleep(2)  # 等待应用完全初始化

        print("\nAPI健康检查:")
        out, _ = execute(ssh, "curl -s http://localhost:3001/api/health")
        if "ok" in out or "status" in out:
            print("✓ API正常")

        print("\n首页访问:")
        out, _ = execute(ssh, "curl -s -o /dev/null -w 'HTTP %{http_code}' http://localhost:3001/")
        status = out.strip()
        print(status)

        if "200" in status:
            print("✓ 首页访问正常!")
        else:
            print(f"⚠ 首页返回 {status}")
            # 查看更详细的响应
            print("\n详细响应:")
            execute(ssh, "curl -v http://localhost:3001/ 2>&1 | head -30")

        # 7. 测试其他端点
        print("\n【7】测试其他端点")
        endpoints = [
            "/api/health",
            "/login",
            "/platform"
        ]

        for endpoint in endpoints:
            out, _ = execute(ssh, f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:3001{endpoint}", show=False)
            status_code = out.strip()
            status_icon = "✓" if status_code in ["200", "302"] else "✗"
            print(f"  {status_icon} {endpoint}: HTTP {status_code}")

        # 8. 显示日志
        print("\n【8】查看最新日志")
        execute(ssh, f"tail -15 {DEPLOY_DIR}/logs/error.log || echo '无错误日志'")

        # 9. 完成
        print("\n" + "=" * 60)
        print("  部署完成!")
        print("=" * 60)
        print(f"\n外部访问地址:")
        print(f"  主页: http://{SERVER}:3001")
        print(f"  登录: http://{SERVER}:3001/login")
        print(f"  平台: http://{SERVER}:3001/platform")
        print(f"  API: http://{SERVER}:3001/api/health")

        print(f"\n管理命令:")
        print(f"  查看日志: ssh {USER}@{SERVER} 'tail -f {DEPLOY_DIR}/logs/error.log'")
        print(f"  重启服务: ssh {USER}@{SERVER} 'pkill -f gunicorn && cd {DEPLOY_DIR} && PYTHONPATH={DEPLOY_DIR}/backend python3 -m gunicorn -w 4 -b 0.0.0.0:3001 backend.app_factory:app'")
        print(f"  停止服务: ssh {USER}@{SERVER} 'pkill -f gunicorn'")

    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == '__main__':
    main()
