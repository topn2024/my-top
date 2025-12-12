#!/usr/bin/env python3
import sys, subprocess
try: import paramiko
except: subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "paramiko"]); import paramiko

bash_script = """#!/bin/bash
set -e

echo "=========================================="
echo "Python 3.14.0 编译安装脚本"
echo "=========================================="

cd /usr/local/src/Python-3.14.0

# 步骤1: 配置
echo -e "\n[1/5] 配置编译选项..."
./configure --enable-optimizations --prefix=/usr/local 2>&1 | tail -10
echo "✓ 配置完成"

# 步骤2: 编译安装
echo -e "\n[2/5] 编译安装Python 3.14.0(需要10-20分钟)..."
echo "TopN@2024" | sudo -S make -j$(nproc) altinstall 2>&1 | tail -20
echo "✓ 编译完成"

# 步骤3: 验证
echo -e "\n[3/5] 验证安装..."
/usr/local/bin/python3.14 --version
echo "✓ 验证成功"

# 步骤4: 更新符号链接
echo -e "\n[4/5] 更新符号链接..."
echo "TopN@2024" | sudo -S ln -sf /usr/local/bin/python3.14 /usr/local/bin/python3
/usr/local/bin/python3 --version
echo "✓ 符号链接已更新"

# 步骤5: 升级pip
echo -e "\n[5/5] 升级pip..."
echo "TopN@2024" | sudo -S /usr/local/bin/python3.14 -m pip install --upgrade pip 2>&1 | tail -5
echo "✓ pip已升级"

echo -e "\n=========================================="
echo "✓✓✓ Python 3.14.0 安装完成! ✓✓✓"
echo "=========================================="
echo ""
echo "使用方法:"
echo "  python3.14 --version"
echo "  python3 --version  (符号链接已更新)"
echo "  python3.14 -m pip install 包名"
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
print("正在连接服务器...")
ssh.connect("39.105.12.124", 22, "u_topn", "TopN@2024", timeout=30)
print("✓ 已连接\n")

print("正在上传安装脚本...")
stdin, stdout, stderr = ssh.exec_command("cat > /tmp/install_python314.sh")
stdin.write(bash_script)
stdin.channel.shutdown_write()
stdout.read()
print("✓ 脚本已上传\n")

print("开始执行安装脚本...\n")
print("="*60)
stdin, stdout, stderr = ssh.exec_command("chmod +x /tmp/install_python314.sh && /tmp/install_python314.sh 2>&1")

for line in stdout:
    print(line.rstrip())

exit_code = stdout.channel.recv_exit_status()
print("="*60)
print(f"\n脚本退出码: {exit_code}")

if exit_code == 0:
    print("\n✓✓✓ Python 3.14.0 安装成功! ✓✓✓")
else:
    print(f"\n✗ 安装失败(退出码{exit_code})")

ssh.close()
