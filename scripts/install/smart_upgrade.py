#!/usr/bin/env python3
"""
智能Python升级 - 检测当前状态并继续
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

def execute_command(ssh, command, description="", sudo_password=None):
    """执行SSH命令并实时显示输出"""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")

    if sudo_password and command.strip().startswith('sudo'):
        command = command.replace('sudo', 'sudo -S', 1)
        stdin, stdout, stderr = ssh.exec_command(command)
        stdin.write(sudo_password + '\n')
        stdin.flush()
    else:
        stdin, stdout, stderr = ssh.exec_command(command)

    for line in stdout:
        print(line.strip())

    error_output = stderr.read().decode('utf-8')
    if error_output and not error_output.startswith('[sudo]'):
        # 只显示非权限拒绝的错误
        if 'Permission denied' not in error_output:
            print(f"错误输出: {error_output}")

    exit_status = stdout.channel.recv_exit_status()
    return exit_status == 0

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    print("正在连接服务器...")
    ssh.connect(SERVER, 22, USERNAME, PASSWORD, timeout=30)
    print("✓ 已连接\n")

    # 检查Python 3.13是否已经安装
    print("="*60)
    print("检查Python 3.13安装状态")
    print("="*60)
    stdin, stdout, stderr = ssh.exec_command("/usr/local/bin/python3.13 --version 2>&1")
    python_check = stdout.read().decode('utf-8').strip()

    if "Python 3.13" in python_check:
        print(f"✓ {python_check} 已经安装!")

        # 更新符号链接
        execute_command(ssh,
            "sudo ln -sf /usr/local/bin/python3.13 /usr/local/bin/python3 && /usr/local/bin/python3 --version",
            "更新python3符号链接",
            sudo_password=PASSWORD)

        # 清理
        execute_command(ssh,
            "sudo rm -rf /tmp/Python-3.13.1 /tmp/Python-3.13.1.tgz && echo '清理完成'",
            "清理临时文件",
            sudo_password=PASSWORD)

        print("\n" + "="*60)
        print("✓ Python 3.13.1 已完成升级!")
        print("="*60)

    else:
        print(f"Python 3.13未安装，检测结果: {python_check}")
        print("需要继续安装流程...")

        # 清理旧的编译目录(使用sudo)
        execute_command(ssh,
            "sudo rm -rf /tmp/Python-3.13.1",
            "清理旧的编译目录",
            sudo_password=PASSWORD)

        # 检查是否已下载源码
        stdin, stdout, stderr = ssh.exec_command("test -f /tmp/Python-3.13.1.tgz && echo 'EXISTS' || echo 'NOT_EXISTS'")
        exists = stdout.read().decode('utf-8').strip()

        if exists == 'NOT_EXISTS':
            execute_command(ssh,
                "cd /tmp && wget --progress=bar:force https://www.python.org/ftp/python/3.13.1/Python-3.13.1.tgz 2>&1",
                "下载Python 3.13.1源码")
        else:
            print("\n✓ Python源码已存在")

        # 解压
        execute_command(ssh,
            "cd /tmp && tar -xzf Python-3.13.1.tgz",
            "解压Python源码")

        # 配置
        print("\n" + "="*60)
        print("配置Python编译选项")
        print("="*60)
        stdin, stdout, stderr = ssh.exec_command("cd /tmp/Python-3.13.1 && ./configure --enable-optimizations --prefix=/usr/local 2>&1 | tail -30")
        for line in stdout:
            print(line.strip())

        # 编译安装
        print("\n" + "="*60)
        print("开始编译安装Python 3.13.1")
        print("预计需要10-20分钟,请耐心等待...")
        print("="*60)

        # 使用sudo make编译
        stdin, stdout, stderr = ssh.exec_command(f"echo '{PASSWORD}' | sudo -S sh -c 'cd /tmp/Python-3.13.1 && make -j$(nproc) altinstall'", get_pty=True)

        # 实时显示编译进度
        import select
        import time

        last_output_time = time.time()
        while True:
            if stdout.channel.exit_status_ready():
                break

            # 使用select检查是否有可读数据
            rl, wl, xl = select.select([stdout.channel], [], [], 1.0)
            if rl:
                try:
                    data = stdout.channel.recv(1024).decode('utf-8', errors='ignore')
                    if data:
                        print(data, end='', flush=True)
                        last_output_time = time.time()
                except:
                    pass

            # 显示等待提示
            if time.time() - last_output_time > 30:
                print(".", end='', flush=True)
                last_output_time = time.time()

        # 获取剩余输出
        remaining = stdout.read().decode('utf-8', errors='ignore')
        if remaining:
            print(remaining)

        # 验证安装
        execute_command(ssh,
            "/usr/local/bin/python3.13 --version",
            "验证Python 3.13.1安装")

        # 升级pip
        execute_command(ssh,
            "sudo /usr/local/bin/python3.13 -m pip install --upgrade pip",
            "升级pip",
            sudo_password=PASSWORD)

        # 更新符号链接
        execute_command(ssh,
            "sudo ln -sf /usr/local/bin/python3.13 /usr/local/bin/python3 && /usr/local/bin/python3 --version",
            "更新python3符号链接",
            sudo_password=PASSWORD)

        # 清理
        execute_command(ssh,
            "sudo rm -rf /tmp/Python-3.13.1 /tmp/Python-3.13.1.tgz",
            "清理临时文件",
            sudo_password=PASSWORD)

        print("\n" + "="*60)
        print("✓ Python升级完成!")
        print("="*60)

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
finally:
    ssh.close()
