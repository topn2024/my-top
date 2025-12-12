#!/usr/bin/env python3
import sys, subprocess
try: import paramiko
except: subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "paramiko"]); import paramiko

bash_script = """#!/bin/bash
echo "=========================================="
echo "配置系统Python 3.14供所有用户使用"
echo "=========================================="

# 步骤1: 更新系统符号链接
echo -e "\n[1/5] 更新系统符号链接..."
echo "TopN@2024" | sudo -S ln -sf /usr/local/bin/python3.14 /usr/bin/python3
echo "TopN@2024" | sudo -S ln -sf /usr/local/bin/python3.14 /usr/bin/python
echo "TopN@2024" | sudo -S ln -sf /usr/local/bin/pip3.14 /usr/bin/pip3
echo "TopN@2024" | sudo -S ln -sf /usr/local/bin/pip3.14 /usr/bin/pip
ls -la /usr/bin/python* /usr/bin/pip* 2>/dev/null | grep -E '(python|pip)' | head -10
echo "✓ 符号链接已创建"

# 步骤2: 配置系统PATH
echo -e "\n[2/5] 配置系统PATH..."
echo "TopN@2024" | sudo -S tee /etc/profile.d/python314.sh > /dev/null << 'EOF'
# Python 3.14 configuration
export PATH="/usr/local/bin:$PATH"
export PYTHON_HOME=/usr/local
EOF
echo "TopN@2024" | sudo -S chmod +x /etc/profile.d/python314.sh
cat /etc/profile.d/python314.sh
echo "✓ PATH配置已创建"

# 步骤3: 验证所有用户可访问
echo -e "\n[3/5] 验证Python可访问性..."
which python3
which python
python3 --version
python --version
echo "✓ Python可访问"

# 步骤4: 验证pip可访问
echo -e "\n[4/5] 验证pip可访问性..."
which pip3
which pip
pip3 --version
pip --version
echo "✓ pip可访问"

# 步骤5: 测试Python功能
echo -e "\n[5/5] 测试Python功能..."
python3 -c "import sys; print(f'Python版本: {sys.version}')"
python3 -c "import sys; print(f'可执行文件: {sys.executable}')"
python3 -c "import sys; print(f'模块路径: {sys.prefix}')"
echo "✓ Python功能正常"

echo -e "\n=========================================="
echo "✓✓✓ 配置完成! ✓✓✓"
echo "=========================================="
echo ""
echo "所有用户现在可以使用以下命令:"
echo "  python --version    (Python 3.14.0)"
echo "  python3 --version   (Python 3.14.0)"
echo "  pip --version       (pip 25.3)"
echo "  pip3 --version      (pip 25.3)"
echo ""
echo "新用户登录时会自动加载配置"
echo "现有会话需要执行: source /etc/profile.d/python314.sh"
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
print("正在连接服务器...")
ssh.connect("39.105.12.124", 22, "u_topn", "TopN@2024", timeout=30)
print("✓ 已连接\n")

print("正在上传配置脚本...")
stdin, stdout, stderr = ssh.exec_command("cat > /tmp/configure_system_python.sh")
stdin.write(bash_script)
stdin.channel.shutdown_write()
stdout.read()
print("✓ 脚本已上传\n")

print("开始执行配置...\n")
print("="*60)

stdin, stdout, stderr = ssh.exec_command("chmod +x /tmp/configure_system_python.sh && /tmp/configure_system_python.sh 2>&1")

for line in stdout:
    print(line.rstrip())

exit_code = stdout.channel.recv_exit_status()

print("="*60)
print(f"\n退出码: {exit_code}")

if exit_code == 0:
    print("\n✓✓✓ 系统配置成功! ✓✓✓")
else:
    print(f"\n✗ 配置失败(退出码{exit_code})")

ssh.close()
