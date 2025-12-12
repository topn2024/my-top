#!/usr/bin/env python3
"""
检查依赖安装状态并继续升级
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
        print(f"错误输出: {error_output}")

    exit_status = stdout.channel.recv_exit_status()
    return exit_status == 0

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    print("正在连接服务器...")
    ssh.connect(SERVER, 22, USERNAME, PASSWORD, timeout=30)
    print("✓ 已连接\n")

    # 检查gcc是否已安装(说明依赖安装成功)
    execute_command(ssh, "gcc --version 2>&1 | head -1", "检查gcc是否已安装")

    # 检查wget是否已安装
    execute_command(ssh, "wget --version 2>&1 | head -1", "检查wget是否已安装")

    # 检查是否已经下载Python源码
    execute_command(ssh, "ls -lh /tmp/Python-3.13.1* 2>&1", "检查/tmp目录中的Python文件")

    # 继续执行Python升级的后续步骤
    print("\n" + "="*60)
    print("开始继续Python升级流程...")
    print("="*60)

    # 下载Python源码(如果还没下载)
    stdin, stdout, stderr = ssh.exec_command("test -f /tmp/Python-3.13.1.tgz && echo 'EXISTS' || echo 'NOT_EXISTS'")
    exists = stdout.read().decode('utf-8').strip()

    if exists == 'NOT_EXISTS':
        execute_command(ssh,
            "cd /tmp && wget -q --show-progress https://www.python.org/ftp/python/3.13.1/Python-3.13.1.tgz 2>&1",
            "下载Python 3.13.1源码")
    else:
        print("\n✓ Python源码已存在,跳过下载")

    # 解压(强制重新解压)
    execute_command(ssh,
        "cd /tmp && rm -rf Python-3.13.1 && tar -xzf Python-3.13.1.tgz",
        "解压Python源码")

    # 配置
    execute_command(ssh,
        "cd /tmp/Python-3.13.1 && ./configure --enable-optimizations --prefix=/usr/local 2>&1 | tail -20",
        "配置Python编译选项(显示最后20行)")

    # 编译安装
    print("\n" + "="*60)
    print("开始编译安装Python 3.13.1(需要10-20分钟)")
    print("="*60)

    execute_command(ssh,
        "cd /tmp/Python-3.13.1 && sudo make -j$(nproc) altinstall 2>&1 | grep -E '(Installing|Collecting|Successfully|Error|error|Python)'",
        "编译安装Python(显示关键信息)",
        sudo_password=PASSWORD)

    # 验证安装
    execute_command(ssh,
        "/usr/local/bin/python3.13 --version",
        "验证Python 3.13.1安装")

    # 升级pip
    execute_command(ssh,
        "sudo /usr/local/bin/python3.13 -m pip install --upgrade pip 2>&1 | tail -10",
        "升级pip",
        sudo_password=PASSWORD)

    # 更新符号链接
    execute_command(ssh,
        "sudo ln -sf /usr/local/bin/python3.13 /usr/local/bin/python3 && /usr/local/bin/python3 --version",
        "更新python3符号链接",
        sudo_password=PASSWORD)

    # 清理
    execute_command(ssh,
        "cd /tmp && rm -rf Python-3.13.1 Python-3.13.1.tgz && echo '清理完成'",
        "清理临时文件")

    print("\n" + "="*60)
    print("✓ Python升级完成！")
    print("="*60)

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
finally:
    ssh.close()
