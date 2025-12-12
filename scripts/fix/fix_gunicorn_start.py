#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 gunicorn 启动问题
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
        print(f"\n执行: {cmd}")
        print("-" * 60)
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    if show and output:
        print(output)
    if show and error and "sudo" not in error.lower():
        print(f"stderr: {error}")
    return output, error

def main():
    print("=" * 60)
    print("  修复 Gunicorn 启动问题")
    print("=" * 60)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=10)
        print("✓ 已连接到服务器\n")

        # 1. 停止现有服务
        print("【1】停止现有服务")
        execute(ssh, "pkill -f gunicorn; sleep 2")
        execute(ssh, "ps aux | grep gunicorn | grep -v grep || echo '✓ 已停止'")

        # 2. 检查 gunicorn 位置
        print("\n【2】检查 gunicorn ")
        execute(ssh, "which gunicorn")
        execute(ssh, "python3 -m gunicorn --version")

        # 3. 使用简化的启动命令(不使用配置文件)
        print("\n【3】使用简化命令启动服务")
        start_cmd = f"cd {DEPLOY_DIR} && nohup python3 -m gunicorn -w 4 -b 0.0.0.0:3001 --timeout 120 --access-logfile logs/access.log --error-logfile logs/error.log 'backend.app_factory:app' > logs/gunicorn_startup.log 2>&1 &"
        execute(ssh, start_cmd)

        # 4. 等待启动
        print("\n【4】等待服务启动...")
        time.sleep(3)

        # 5. 检查进程
        print("\n【5】检查进程状态")
        execute(ssh, "ps aux | grep gunicorn | grep -v grep")

        # 6. 检查端口
        print("\n【6】检查端口监听")
        execute(ssh, "ss -tlnp | grep :3001")

        # 7. 测试访问
        print("\n【7】测试 HTTP 访问")
        execute(ssh, "curl -s http://localhost:3001/api/health")
        out, _ = execute(ssh, "curl -s -o /dev/null -w '%{http_code}' http://localhost:3001/", show=False)
        print(f"首页状态码: {out.strip()}")

        if "200" in out:
            print("\n✓ 服务启动成功!")
        else:
            print("\n⚠ 首页仍返回非200状态码,查看错误日志:")
            execute(ssh, f"tail -50 {DEPLOY_DIR}/logs/error.log")

        # 8. 外部访问提示
        print("\n【8】外部访问测试")
        print(f"   浏览器访问: http://{SERVER}:3001")
        print(f"   API测试: http://{SERVER}:3001/api/health")

    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == '__main__':
    main()
