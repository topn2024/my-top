#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
强制重启服务
"""

import paramiko
import sys
import io
import time

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

SERVER = "39.105.12.124"
USER = "u_topn"
PASSWORD = "TopN@2024"
DEPLOY_DIR = "/home/u_topn/TOP_N"

def main():
    print("=" * 80)
    print("  强制重启服务")
    print("=" * 80)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=10)

    # 1. 彻底停止所有服务
    print("\n【1】停止所有服务")
    cmds = [
        "pkill -9 -f gunicorn",
        "pkill -9 -f 'app_factory|app_with_upload'",
        f"echo {PASSWORD} | sudo -S fuser -k 3001/tcp 2>/dev/null || true",
        "sleep 3"
    ]

    for cmd in cmds:
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
        stdout.read()

    print("  ✓ 已停止所有服务")

    # 2. 验证文件已上传
    print("\n【2】验证文件")
    stdin, stdout, stderr = ssh.exec_command(f"ls -lh {DEPLOY_DIR}/templates/platform.html")
    out = stdout.read().decode('utf-8', errors='ignore')
    if "platform.html" in out:
        print("  ✓ platform.html 存在")
    else:
        print("  ✗ platform.html 不存在")

    stdin, stdout, stderr = ssh.exec_command(f"ls -lh {DEPLOY_DIR}/backend/blueprints/auth.py")
    out = stdout.read().decode('utf-8', errors='ignore')
    if "auth.py" in out:
        print("  ✓ auth.py 存在")

    # 3. 清理日志
    print("\n【3】清理旧日志")
    stdin, stdout, stderr = ssh.exec_command(f"rm -f {DEPLOY_DIR}/logs/*.log")
    stdout.read()
    print("  ✓ 日志已清理")

    # 4. 启动服务(使用更简单的方法)
    print("\n【4】启动服务")

    start_cmd = f"""
cd {DEPLOY_DIR} && \\
PYTHONPATH={DEPLOY_DIR}/backend:{DEPLOY_DIR}:$PYTHONPATH \\
nohup python3 -m gunicorn \\
  -w 4 \\
  -b 0.0.0.0:3001 \\
  --timeout 120 \\
  --access-logfile logs/access.log \\
  --error-logfile logs/error.log \\
  --log-level info \\
  'backend.app_factory:app' \\
  > logs/startup.log 2>&1 &
"""

    stdin, stdout, stderr = ssh.exec_command(start_cmd, timeout=5)
    print("  启动命令已执行")

    # 5. 等待启动
    print("\n【5】等待服务启动...")
    for i in range(8):
        time.sleep(1)
        stdin, stdout, stderr = ssh.exec_command("ps aux | grep gunicorn | grep -v grep | wc -l")
        count = stdout.read().decode('utf-8', errors='ignore').strip()
        if int(count) > 0:
            print(f"  ✓ 服务已启动 (进程数: {count})")
            break
        print(f"    等待中... ({i+1}/8)")
    else:
        print("  ⚠ 服务启动可能失败")
        stdin, stdout, stderr = ssh.exec_command(f"tail -20 {DEPLOY_DIR}/logs/error.log")
        print(stdout.read().decode('utf-8', errors='ignore'))
        return

    # 6. 测试各个端点
    print("\n【6】测试端点")
    time.sleep(2)

    tests = [
        ("首页", "curl -s -o /dev/null -w '%{http_code}' http://localhost:3001/"),
        ("平台页", "curl -s -o /dev/null -w '%{http_code}' http://localhost:3001/platform"),
        ("登录页", "curl -s -o /dev/null -w '%{http_code}' http://localhost:3001/login"),
        ("健康检查", "curl -s http://localhost:3001/api/health"),
    ]

    results = {}
    for name, cmd in tests:
        stdin, stdout, stderr = ssh.exec_command(cmd)
        result = stdout.read().decode('utf-8', errors='ignore').strip()
        results[name] = result

        if "health" in cmd:
            print(f"  {name}: {result[:50]}")
        else:
            status = "✓" if result == "200" else "✗"
            print(f"  {status} {name}: HTTP {result}")

    # 7. 总结
    print("\n" + "=" * 80)
    if all(r == "200" or "ok" in r for r in results.values()):
        print("  ✅ 服务启动成功,所有测试通过!")
        print("=" * 80)
        print(f"\n访问地址: http://{SERVER}:3001")
    else:
        print("  ⚠ 部分测试未通过")
        print("=" * 80)
        print("\n查看错误日志:")
        stdin, stdout, stderr = ssh.exec_command(f"tail -30 {DEPLOY_DIR}/logs/error.log")
        print(stdout.read().decode('utf-8', errors='ignore'))

    ssh.close()

if __name__ == '__main__':
    main()
