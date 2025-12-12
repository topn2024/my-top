#!/usr/bin/env python3
import sys, subprocess, time
try: import paramiko
except: subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "paramiko"]); import paramiko

bash_script = """#!/bin/bash
echo "=========================================="
echo "Python 3.14.0 标准编译安装"
echo "=========================================="

cd /usr/local/src/Python-3.14.0

# 清理之前的编译
echo -e "\n[1/6] 清理之前的编译文件..."
echo "TopN@2024" | sudo -S make clean 2>&1 | tail -3 || echo "无需清理"
echo "✓ 清理完成"

# 配置(不使用优化)
echo -e "\n[2/6] 配置编译选项(标准模式)..."
./configure --prefix=/usr/local 2>&1 | tail -5
echo "✓ 配置完成"

# 编译
echo -e "\n[3/6] 编译Python 3.14.0(需要5-10分钟)..."
echo "开始时间: $(date '+%H:%M:%S')"
echo "TopN@2024" | sudo -S make -j$(nproc) 2>&1 | tail -15
echo "✓ 编译完成"

# 安装
echo -e "\n[4/6] 安装Python 3.14.0..."
echo "TopN@2024" | sudo -S make altinstall 2>&1 | grep -E '(Installing|Collecting|Successfully)' | tail -10
echo "✓ 安装完成"

# 验证
echo -e "\n[5/6] 验证安装..."
/usr/local/bin/python3.14 --version
/usr/local/bin/python3.14 -c "import sys; print(f'Python位置: {sys.executable}')"
echo "✓ 验证成功"

# 更新符号链接
echo -e "\n[6/6] 更新符号链接和pip..."
echo "TopN@2024" | sudo -S ln -sf /usr/local/bin/python3.14 /usr/local/bin/python3
echo "TopN@2024" | sudo -S /usr/local/bin/python3.14 -m ensurepip --upgrade 2>&1 | tail -3
echo "TopN@2024" | sudo -S /usr/local/bin/python3.14 -m pip install --upgrade pip 2>&1 | tail -3
/usr/local/bin/python3 --version
echo "✓ 更新完成"

echo -e "\n=========================================="
echo "✓✓✓ Python 3.14.0 安装成功! ✓✓✓"
echo "=========================================="
echo ""
echo "使用方法:"
echo "  python3.14 --version"
echo "  python3 --version"
echo "  python3.14 -m pip install <package>"
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
print("正在连接服务器...")
ssh.connect("39.105.12.124", 22, "u_topn", "TopN@2024", timeout=30)
print("✓ 已连接\n")

print("正在上传安装脚本...")
stdin, stdout, stderr = ssh.exec_command("cat > /tmp/install_python314_std.sh")
stdin.write(bash_script)
stdin.channel.shutdown_write()
stdout.read()
print("✓ 脚本已上传\n")

print("开始执行安装脚本(预计5-10分钟)...\n")
print("="*60)
start_time = time.time()

stdin, stdout, stderr = ssh.exec_command("chmod +x /tmp/install_python314_std.sh && /tmp/install_python314_std.sh 2>&1")

for line in stdout:
    print(line.rstrip())

exit_code = stdout.channel.recv_exit_status()
elapsed = int(time.time() - start_time)

print("="*60)
print(f"\n总耗时: {elapsed}秒 ({elapsed//60}分{elapsed%60}秒)")
print(f"退出码: {exit_code}")

if exit_code == 0:
    print("\n✓✓✓ Python 3.14.0 安装成功! ✓✓✓")
else:
    print(f"\n✗ 安装失败(退出码{exit_code})")

ssh.close()
