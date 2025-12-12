#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动编译安装Python 3.9
"""
import paramiko
import time
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

def main():
    try:
        print("=" * 80)
        print("手动编译安装Python 3.9.18 (稳定版)")
        print("=" * 80)

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("\n✓ SSH连接成功\n")

        # 完整的编译安装脚本
        install_script = """
set -e

echo "================================================================================"
echo "步骤1: 安装编译依赖"
echo "================================================================================"
sudo yum install -y gcc openssl-devel bzip2-devel libffi-devel zlib-devel wget make sqlite-devel

echo ""
echo "================================================================================"
echo "步骤2: 下载Python 3.9.18源码"
echo "================================================================================"
cd /tmp
if [ ! -f Python-3.9.18.tgz ]; then
    wget https://www.python.org/ftp/python/3.9.18/Python-3.9.18.tgz
fi

echo ""
echo "================================================================================"
echo "步骤3: 解压源码"
echo "================================================================================"
tar xzf Python-3.9.18.tgz
cd Python-3.9.18

echo ""
echo "================================================================================"
echo "步骤4: 配置编译选项 (这可能需要2-3分钟)"
echo "================================================================================"
./configure --enable-optimizations --prefix=/usr/local/python39

echo ""
echo "================================================================================"
echo "步骤5: 编译Python (这可能需要10-15分钟，请耐心等待...)"
echo "================================================================================"
sudo make altinstall

echo ""
echo "================================================================================"
echo "步骤6: 验证安装"
echo "================================================================================"
/usr/local/python39/bin/python3.9 --version

echo ""
echo "================================================================================"
echo "Python 3.9.18 安装完成!"
echo "================================================================================"
"""

        print("开始执行编译安装...")
        print("注意: 整个过程需要15-20分钟，请耐心等待...")
        print("")

        stdin, stdout, stderr = ssh.exec_command(install_script, timeout=1800)  # 30分钟超时

        # 实时读取输出
        print("安装日志:")
        print("-" * 80)

        import select

        while not stdout.channel.exit_status_ready():
            if stdout.channel.recv_ready():
                data = stdout.channel.recv(1024).decode('utf-8', errors='ignore')
                print(data, end='', flush=True)
            time.sleep(0.1)

        # 读取剩余输出
        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')

        print(output)

        if error:
            print("\n错误信息:")
            print(error[:1000])

        print("\n" + "="*80)
        print("完成!")
        print("=" *80)

        # 验证安装
        print("\n验证Python 3.9安装:")
        stdin, stdout, stderr = ssh.exec_command("/usr/local/python39/bin/python3.9 --version", timeout=10)
        version_output = stdout.read().decode('utf-8')
        print(f"  {version_output}")

        if "Python 3.9" in version_output:
            print("\n✓ Python 3.9 安装成功!")
            print("\n下一步: 运行 deploy_ultimate_solution_v2.py 创建虚拟环境并安装依赖")
        else:
            print("\n⚠ Python 3.9 安装可能有问题，请检查日志")

        ssh.close()

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
