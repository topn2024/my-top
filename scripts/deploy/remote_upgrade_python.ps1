# PowerShell脚本：远程升级服务器Python
# 服务器信息
$server = "39.105.12.124"
$username = "u_topn"
$password = "TopN@2024"

Write-Host "=== 远程升级服务器Python到3.13.1 ===" -ForegroundColor Green
Write-Host ""

# 创建远程命令脚本
$commands = @"
# 检查当前Python版本
echo '=== 当前Python版本 ==='
python3 --version 2>&1

# 检查系统类型
if [ -f /etc/redhat-release ]; then
    OS_TYPE='centos'
    echo '检测到CentOS/RHEL系统'
elif [ -f /etc/debian_version ]; then
    OS_TYPE='debian'
    echo '检测到Debian/Ubuntu系统'
fi

# 安装依赖
echo '=== 安装编译依赖 ==='
if [ "\$OS_TYPE" = "centos" ]; then
    sudo yum groupinstall -y 'Development Tools'
    sudo yum install -y gcc openssl-devel bzip2-devel libffi-devel zlib-devel wget
else
    sudo apt update
    sudo apt install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev wget
fi

# 下载Python 3.13.1
echo '=== 下载Python 3.13.1 ==='
cd /tmp
wget -q https://www.python.org/ftp/python/3.13.1/Python-3.13.1.tgz
tar -xzf Python-3.13.1.tgz
cd Python-3.13.1

# 编译安装
echo '=== 编译安装Python 3.13.1（需要约10-15分钟） ==='
./configure --enable-optimizations --prefix=/usr/local
sudo make altinstall

# 验证安装
echo '=== 验证安装 ==='
/usr/local/bin/python3.13 --version

# 更新符号链接（可选）
echo '=== 更新python3符号链接 ==='
sudo ln -sf /usr/local/bin/python3.13 /usr/bin/python3
python3 --version

# 清理
cd /tmp
rm -rf Python-3.13.1*

echo '=== Python升级完成 ==='
"@

Write-Host "请手动执行以下步骤：" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. 打开新的终端窗口" -ForegroundColor Cyan
Write-Host "2. 执行SSH连接命令：" -ForegroundColor Cyan
Write-Host "   ssh $username@$server" -ForegroundColor White
Write-Host "3. 输入密码：$password" -ForegroundColor White
Write-Host "4. 连接成功后，复制并执行以下完整脚本：" -ForegroundColor Cyan
Write-Host ""
Write-Host $commands -ForegroundColor Gray
Write-Host ""
Write-Host "或者将脚本保存到文件后执行：" -ForegroundColor Cyan
Write-Host "   cat > /tmp/upgrade_python.sh << 'EOF'" -ForegroundColor White
Write-Host $commands -ForegroundColor Gray
Write-Host "EOF" -ForegroundColor White
Write-Host "   chmod +x /tmp/upgrade_python.sh" -ForegroundColor White
Write-Host "   /tmp/upgrade_python.sh" -ForegroundColor White
