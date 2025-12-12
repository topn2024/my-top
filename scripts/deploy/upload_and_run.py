import sys, subprocess
try: import paramiko
except: subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "paramiko"]); import paramiko

# 创建服务器端安装脚本
bash_script = """#!/bin/bash
set -e
echo "=========================================="
echo "Python 3.13.1 自动安装脚本"
echo "=========================================="

cd /tmp

# 步骤1: 下载
echo -e "\n[1/7] 下载Python 3.13.1源码..."
wget -q --show-progress -O Python-3.13.1.tgz https://www.python.org/ftp/python/3.13.1/Python-3.13.1.tgz
ls -lh Python-3.13.1.tgz
echo "✓ 下载完成"

# 步骤2: 解压
echo -e "\n[2/7] 解压源码..."
tar -xzf Python-3.13.1.tgz
echo "✓ 解压完成"

# 步骤3: 配置
echo -e "\n[3/7] 配置编译选项..."
cd Python-3.13.1
./configure --enable-optimizations --prefix=/usr/local > /tmp/config.log 2>&1
echo "✓ 配置完成"

# 步骤4: 编译安装
echo -e "\n[4/7] 编译安装(需要10-20分钟)..."
echo "TopN@2024" | sudo -S make -j$(nproc) altinstall > /tmp/make.log 2>&1
echo "✓ 编译完成"

# 步骤5: 验证
echo -e "\n[5/7] 验证安装..."
/usr/local/bin/python3.13 --version
echo "✓ 验证成功"

# 步骤6: 更新符号链接
echo -e "\n[6/7] 更新符号链接..."
echo "TopN@2024" | sudo -S ln -sf /usr/local/bin/python3.13 /usr/local/bin/python3
/usr/local/bin/python3 --version
echo "✓ 符号链接已更新"

# 步骤7: 清理
echo -e "\n[7/7] 清理临时文件..."
cd /tmp
echo "TopN@2024" | sudo -S rm -rf Python-3.13.1 Python-3.13.1.tgz
echo "✓ 清理完成"

echo -e "\n=========================================="
echo "✓✓✓ Python 3.13.1 升级完成! ✓✓✓"
echo "=========================================="
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
print("正在连接服务器...")
ssh.connect("39.105.12.124", 22, "u_topn", "TopN@2024", timeout=30)
print("✓ 已连接\n")

# 上传脚本
print("正在上传安装脚本...")
stdin, stdout, stderr = ssh.exec_command("cat > /tmp/install_python313.sh")
stdin.write(bash_script)
stdin.channel.shutdown_write()
stdout.read()
print("✓ 脚本已上传\n")

# 赋予执行权限并运行
print("开始执行安装脚本...\n")
stdin, stdout, stderr = ssh.exec_command("chmod +x /tmp/install_python313.sh && /tmp/install_python313.sh 2>&1")

# 实时显示输出
for line in stdout:
    print(line.rstrip())

ssh.close()
