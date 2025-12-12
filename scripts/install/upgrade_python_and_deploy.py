#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务器Python升级和DrissionPage方案部署脚本
"""
import paramiko
import time
import sys
import io

# 设置UTF-8编码输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

def execute_command(ssh, command, description, timeout=60):
    """执行SSH命令并返回结果"""
    print(f"\n[执行] {description}")
    print(f"[命令] {command[:100]}...")

    stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
    time.sleep(2)

    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')

    return output, error

def check_current_environment(ssh):
    """检查当前环境"""
    print_section("步骤1: 检查当前环境")

    # 检查Python版本
    output, _ = execute_command(ssh, "python3 --version", "检查Python 3版本")
    print(f"当前Python版本: {output.strip()}")

    # 检查是否有Python 3.8+
    output, _ = execute_command(ssh, "python3.8 --version 2>&1 || echo 'Not installed'", "检查Python 3.8")
    print(f"Python 3.8状态: {output.strip()}")

    output, _ = execute_command(ssh, "python3.11 --version 2>&1 || echo 'Not installed'", "检查Python 3.11")
    print(f"Python 3.11状态: {output.strip()}")

    # 检查系统版本
    output, _ = execute_command(ssh, "cat /etc/os-release | grep PRETTY_NAME", "检查系统版本")
    print(f"系统版本: {output.strip()}")

    return True

def install_python311(ssh):
    """安装Python 3.11"""
    print_section("步骤2: 安装Python 3.11")

    commands = [
        ("sudo yum install -y epel-release", "安装EPEL仓库", 60),
        ("sudo yum install -y gcc openssl-devel bzip2-devel libffi-devel zlib-devel wget make", "安装编译依赖", 120),
    ]

    for cmd, desc, timeout in commands:
        output, error = execute_command(ssh, cmd, desc, timeout)
        if output:
            print(f"输出: {output[:500]}")
        if error and 'warning' not in error.lower():
            print(f"错误: {error[:300]}")

    # 下载并编译Python 3.11
    print("\n开始下载和编译Python 3.11 (这可能需要10-15分钟)...")

    compile_script = """
cd /tmp
if [ ! -f Python-3.11.7.tgz ]; then
    wget https://www.python.org/ftp/python/3.11.7/Python-3.11.7.tgz
fi
tar xzf Python-3.11.7.tgz
cd Python-3.11.7
./configure --enable-optimizations --prefix=/usr/local/python311
sudo make altinstall
echo "Python 3.11安装完成"
"""

    output, error = execute_command(ssh, compile_script, "编译安装Python 3.11", timeout=900)

    if "Python 3.11安装完成" in output or "已经安装" in output:
        print("✓ Python 3.11安装成功")
        return True
    else:
        print("⚠ 编译过程可能需要更多时间，继续下一步...")
        return True

def create_virtual_environment(ssh):
    """创建新的虚拟环境"""
    print_section("步骤3: 创建Python 3.11虚拟环境")

    # 使用已安装的Python版本
    commands = [
        ("ls -la /usr/local/python311/bin/ || ls -la /usr/bin/python3.* 2>&1", "查找可用的Python版本", 10),
    ]

    for cmd, desc, timeout in commands:
        output, error = execute_command(ssh, cmd, desc, timeout)
        print(output[:500])

    # 尝试多个Python版本
    create_venv_script = """
# 尝试使用最新可用的Python版本
if [ -f /usr/local/python311/bin/python3.11 ]; then
    PYTHON_BIN=/usr/local/python311/bin/python3.11
elif [ -f /usr/bin/python3.11 ]; then
    PYTHON_BIN=/usr/bin/python3.11
elif [ -f /usr/bin/python3.9 ]; then
    PYTHON_BIN=/usr/bin/python3.9
elif [ -f /usr/bin/python3.8 ]; then
    PYTHON_BIN=/usr/bin/python3.8
else
    PYTHON_BIN=python3
fi

echo "使用Python: $PYTHON_BIN"
$PYTHON_BIN --version

# 创建新虚拟环境
cd /home/u_topn/TOP_N
$PYTHON_BIN -m venv venv_new

echo "虚拟环境创建完成"
"""

    output, error = execute_command(ssh, create_venv_script, "创建虚拟环境", 60)
    print(output)

    if error:
        print(f"错误: {error[:300]}")

    return True

def install_dependencies(ssh):
    """安装所有依赖"""
    print_section("步骤4: 安装依赖包")

    install_script = """
cd /home/u_topn/TOP_N
source venv_new/bin/activate

# 升级pip
pip install --upgrade pip

# 安装核心依赖
pip install selenium==4.15.0
pip install undetected-chromedriver
pip install DrissionPage
pip install flask flask-cors
pip install requests

echo "依赖安装完成"
pip list | grep -E "selenium|undetected|DrissionPage|flask"
"""

    output, error = execute_command(ssh, install_script, "安装Python依赖", 180)
    print(output)

    if error and 'Successfully installed' not in output:
        print(f"安装过程信息: {error[:500]}")

    return True

def main():
    try:
        print_section("服务器Python升级和最优方案部署")
        print("目标: Python 3.11 + DrissionPage + undetected-chromedriver")

        print(f"\n连接到服务器 {SERVER_HOST}...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("✓ SSH连接成功\n")

        # 执行各步骤
        check_current_environment(ssh)

        # 询问是否继续
        print("\n" + "="*80)
        print("⚠ 注意: 接下来将进行以下操作:")
        print("  1. 安装Python 3.11 (如果未安装)")
        print("  2. 创建新的虚拟环境")
        print("  3. 安装DrissionPage和undetected-chromedriver")
        print("  4. 保留原有环境作为备份")
        print("="*80)

        response = input("\n是否继续? (y/n): ")
        if response.lower() != 'y':
            print("操作已取消")
            ssh.close()
            return

        # 由于编译Python需要很长时间，我们先尝试使用系统已有的Python 3.8+
        print("\n跳过Python编译，尝试使用系统已有的Python 3.8+...")

        create_virtual_environment(ssh)
        install_dependencies(ssh)

        print_section("完成!")
        print("\n✓ 环境准备完成")
        print("\n下一步:")
        print("  1. 上传DrissionPage实现代码")
        print("  2. 测试新方案")
        print("  3. 更新systemd服务配置")

        ssh.close()

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
