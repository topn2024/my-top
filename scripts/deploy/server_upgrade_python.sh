#!/bin/bash
# 服务器Python升级脚本
# 此脚本需要在远程服务器上执行

echo "=== 开始升级Python到3.13.1 ==="
echo ""

# 检查当前Python版本
echo "1. 检查当前Python版本："
python3 --version 2>&1 || echo "python3 未安装"
echo ""

# 检测操作系统类型
echo "2. 检测操作系统类型："
if [ -f /etc/redhat-release ]; then
    OS_TYPE="centos"
    echo "检测到: CentOS/RHEL"
elif [ -f /etc/debian_version ]; then
    OS_TYPE="debian"
    echo "检测到: Debian/Ubuntu"
else
    echo "未知操作系统"
    exit 1
fi
echo ""

# 安装编译依赖
echo "3. 安装编译依赖..."
if [ "$OS_TYPE" = "centos" ]; then
    sudo yum groupinstall -y 'Development Tools'
    sudo yum install -y gcc openssl-devel bzip2-devel libffi-devel zlib-devel wget sqlite-devel
else
    sudo apt update
    sudo apt install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev \
        libnss3-dev libssl-dev libreadline-dev libffi-dev wget libsqlite3-dev
fi
echo ""

# 下载Python 3.13.1源码
echo "4. 下载Python 3.13.1源码..."
cd /tmp
if [ -f Python-3.13.1.tgz ]; then
    echo "源码包已存在，跳过下载"
else
    wget https://www.python.org/ftp/python/3.13.1/Python-3.13.1.tgz
fi
echo ""

# 解压
echo "5. 解压源码..."
rm -rf Python-3.13.1
tar -xzf Python-3.13.1.tgz
cd Python-3.13.1
echo ""

# 配置
echo "6. 配置编译选项..."
./configure --enable-optimizations --prefix=/usr/local
echo ""

# 编译（这一步需要较长时间）
echo "7. 编译Python（这可能需要10-20分钟，请耐心等待）..."
sudo make -j$(nproc) altinstall
echo ""

# 验证安装
echo "8. 验证安装..."
if /usr/local/bin/python3.13 --version; then
    echo "✓ Python 3.13.1 安装成功！"
else
    echo "✗ Python 3.13.1 安装失败"
    exit 1
fi
echo ""

# 更新pip
echo "9. 升级pip..."
sudo /usr/local/bin/python3.13 -m pip install --upgrade pip
echo ""

# 创建符号链接（可选）
echo "10. 是否将python3链接到3.13.1？(y/n)"
echo "    注意：这会改变系统默认的python3版本"
echo "    如果不确定，请输入'n'，可以直接使用'python3.13'命令"
read -p "请选择 [y/N]: " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo ln -sf /usr/local/bin/python3.13 /usr/bin/python3
    sudo ln -sf /usr/local/bin/pip3.13 /usr/bin/pip3
    echo "✓ 符号链接已更新"
    python3 --version
else
    echo "跳过符号链接更新，使用 'python3.13' 命令调用新版本"
fi
echo ""

# 清理安装文件
echo "11. 清理临时文件..."
cd /tmp
rm -rf Python-3.13.1
echo ""

echo "=== Python升级完成！ ==="
echo ""
echo "使用方法："
echo "  - 直接使用: python3.13 --version"
echo "  - pip安装包: python3.13 -m pip install 包名"
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "  - 或使用: python3 --version"
fi
