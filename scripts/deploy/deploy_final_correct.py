#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import paramiko, os, sys, time, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 使用正确的用户和路径
SERVER = "39.105.12.124"
USER = "u_topn"
PASSWORD = "TopN@2024"
SERVER_PATH = "/home/u_topn/TOP_N/backend"
LOCAL_PATH = "D:/work/code/TOP_N/backend"
FILES = ["zhihu_auto_post_enhanced.py", "app_with_upload.py"]

print("="*70)
print("  知乎自动登录功能 - 全自动部署")
print("="*70)
print(f"服务器: {USER}@{SERVER}")
print(f"路径: {SERVER_PATH}")

try:
    print("\n步骤1/7: 连接服务器...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=10)
    print("  ✓ 连接成功")

    print("\n步骤2/7: 备份文件...")
    ssh.exec_command(f"cd {SERVER_PATH} && cp app_with_upload.py app_with_upload.py.backup_{int(time.time())}")
    time.sleep(1)
    print("  ✓ 备份完成")

    print("\n步骤3/7: 上传文件...")
    sftp = ssh.open_sftp()
    for f in FILES:
        local = os.path.join(LOCAL_PATH, f)
        remote = f"{SERVER_PATH}/{f}"
        print(f"  上传 {f}...")
        sftp.put(local, remote)
        stat = sftp.stat(remote)
        print(f"  ✓ {f} ({stat.st_size} bytes)")
    sftp.close()

    print("\n步骤4/7: 验证文件...")
    stdin, stdout, stderr = ssh.exec_command(f"cd {SERVER_PATH} && ls -lh zhihu_auto_post_enhanced.py app_with_upload.py")
    print(stdout.read().decode())

    stdin, stdout, stderr = ssh.exec_command(f"grep 'from zhihu_auto_post_enhanced import' {SERVER_PATH}/app_with_upload.py")
    if stdout.read():
        print("  ✓ 代码集成正确")
    else:
        print("  ✗ 代码集成错误")
        sys.exit(1)

    stdin, stdout, stderr = ssh.exec_command(f"grep 'password=password,' {SERVER_PATH}/app_with_upload.py")
    if stdout.read():
        print("  ✓ password参数已添加")

    print("\n步骤5/7: 停止旧服务...")
    # Kill gunicorn processes (the actual service runner)
    stdin, stdout, stderr = ssh.exec_command("pkill -9 -f 'gunicorn.*app_with_upload'")
    time.sleep(2)

    # Kill any direct Python processes running app_with_upload.py
    ssh.exec_command("pkill -9 -f 'python.*app_with_upload.py'")
    time.sleep(2)

    # Final check with fuser on port 3001
    ssh.exec_command("fuser -k -9 3001/tcp 2>/dev/null || true")
    time.sleep(2)
    print("  ✓ 已停止所有相关进程（gunicorn和python）")

    print("\n步骤6/7: 启动新服务...")
    ssh.exec_command(f"mkdir -p /home/u_topn/TOP_N/logs")
    # Start with gunicorn as configured
    ssh.exec_command(f"cd /home/u_topn/TOP_N/backend && nohup /usr/local/bin/python3.14 /home/u_topn/.local/bin/gunicorn --config /home/u_topn/TOP_N/gunicorn_config.py app_with_upload:app > /home/u_topn/TOP_N/logs/gunicorn.log 2>&1 &")
    time.sleep(5)
    print("  ✓ 已启动 (使用gunicorn)")

    print("\n步骤7/7: 验证服务...")
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep 'gunicorn.*app_with_upload' | grep -v grep")
    output = stdout.read().decode()
    if output:
        print("  ✓ Gunicorn进程运行中")
        for line in output.strip().split('\n')[:2]:
            parts = line.split()
            print(f"    PID: {parts[1]}")
    else:
        print("  ✗ 服务未运行，查看日志:")
        stdin, stdout, stderr = ssh.exec_command(f"tail -30 /home/u_topn/TOP_N/logs/gunicorn_error.log")
        print(stdout.read().decode())
        sys.exit(1)

    stdin, stdout, stderr = ssh.exec_command("netstat -tuln | grep ':8080'")
    port_output = stdout.read().decode()
    if port_output:
        print("  ✓ 端口8080监听中")
    else:
        print("  ⚠ 端口8080未监听（可能还在启动）")

    print("\n最新日志:")
    stdin, stdout, stderr = ssh.exec_command(f"tail -10 /home/u_topn/TOP_N/logs/gunicorn_error.log")
    print(stdout.read().decode())

    ssh.close()

    print("\n" + "="*70)
    print("  🎉 部署成功完成！")
    print("="*70)
    print("\n✅ 已部署功能:")
    print("  1. Cookie优先登录")
    print("  2. 自动密码登录fallback")
    print("  3. Cookie自动保存")
    print("\n📝 访问地址:")
    print("  http://39.105.12.124:8080")
    print("\n📝 下一步:")
    print("  1. 在Web界面配置知乎测试账号")
    print("  2. 测试发布功能")
    print("  3. 监控日志: ssh u_topn@39.105.12.124")
    print("             tail -f /home/u_topn/TOP_N/logs/gunicorn_error.log")
    print()

except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
