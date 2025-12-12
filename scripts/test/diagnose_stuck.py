#!/usr/bin/env python3
"""
诊断服务器上卡住的安装进程
"""
import sys
try:
    import paramiko
except ImportError:
    print("正在安装paramiko库...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko"])
    import paramiko

SERVER = "39.105.12.124"
USERNAME = "u_topn"
PASSWORD = "TopN@2024"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    print("正在连接服务器...")
    ssh.connect(SERVER, 22, USERNAME, PASSWORD, timeout=30)
    print("✓ 已连接\n")

    # 检查正在运行的yum/rpm进程
    print("="*60)
    print("1. 检查YUM/RPM进程:")
    print("="*60)
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep -E 'yum|rpm|dnf' | grep -v grep")
    output = stdout.read().decode('utf-8')
    if output:
        print(output)
    else:
        print("没有发现yum/rpm进程在运行")

    # 检查yum日志最后几行
    print("\n" + "="*60)
    print("2. 检查YUM日志最后20行:")
    print("="*60)
    stdin, stdout, stderr = ssh.exec_command("sudo tail -20 /var/log/yum.log", get_pty=True)
    stdin.write(PASSWORD + '\n')
    stdin.flush()
    print(stdout.read().decode('utf-8'))

    # 检查yum是否被锁
    print("\n" + "="*60)
    print("3. 检查YUM锁文件:")
    print("="*60)
    stdin, stdout, stderr = ssh.exec_command("ls -lh /var/run/yum.pid 2>&1")
    print(stdout.read().decode('utf-8'))

    # 检查系统负载
    print("\n" + "="*60)
    print("4. 检查系统负载:")
    print("="*60)
    stdin, stdout, stderr = ssh.exec_command("uptime && free -h")
    print(stdout.read().decode('utf-8'))

    # 检查网络连接
    print("\n" + "="*60)
    print("5. 检查网络连接数:")
    print("="*60)
    stdin, stdout, stderr = ssh.exec_command("netstat -an | grep ESTABLISHED | wc -l")
    print(f"活跃连接数: {stdout.read().decode('utf-8').strip()}")

    # 杀死卡住的yum进程
    print("\n" + "="*60)
    print("6. 准备清理卡住的进程...")
    print("="*60)

    stdin, stdout, stderr = ssh.exec_command("pgrep -f 'yum.*groupinstall'")
    pids = stdout.read().decode('utf-8').strip()

    if pids:
        print(f"发现YUM进程PID: {pids}")
        print("正在杀死卡住的yum进程...")
        stdin, stdout, stderr = ssh.exec_command(f"sudo kill -9 {pids}", get_pty=True)
        stdin.write(PASSWORD + '\n')
        stdin.flush()
        print(stdout.read().decode('utf-8'))
        print("✓ 已杀死yum进程")

        # 清理yum锁
        print("\n清理yum锁文件...")
        stdin, stdout, stderr = ssh.exec_command("sudo rm -f /var/run/yum.pid /var/lock/subsys/yum", get_pty=True)
        stdin.write(PASSWORD + '\n')
        stdin.flush()
        print("✓ 已清理锁文件")
    else:
        print("没有发现卡住的yum进程")

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
finally:
    ssh.close()
