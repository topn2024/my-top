#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL数据库自动安装脚本
服务器: 39.105.12.124
"""
import sys
import io
import subprocess

# 设置标准输出为UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
try:
    import paramiko
except ImportError:
    print("正在安装paramiko库...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "paramiko"])
    import paramiko

SERVER = "39.105.12.124"
USERNAME = "u_topn"
PASSWORD = "TopN@2024"

def execute_command(ssh, command, description="", sudo_password=None, show_output=True):
    """执行SSH命令并实时显示输出"""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")

    if sudo_password and 'sudo' in command:
        # 使用echo传递密码给sudo
        command = f"echo '{sudo_password}' | sudo -S {command.replace('sudo', '').strip()}"

    stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)

    if show_output:
        for line in stdout:
            line_text = line.strip()
            if line_text and not line_text.startswith('[sudo]'):
                print(line_text)
    else:
        stdout.read()

    exit_status = stdout.channel.recv_exit_status()
    return exit_status == 0

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    print("正在连接服务器...")
    ssh.connect(SERVER, 22, USERNAME, PASSWORD, timeout=30)
    print("✓ 已连接\n")

    # 步骤1: 检查系统信息
    print("="*60)
    print("步骤1: 检查系统信息")
    print("="*60)
    stdin, stdout, stderr = ssh.exec_command("cat /etc/os-release | grep PRETTY_NAME")
    print(stdout.read().decode('utf-8').strip())

    # 步骤2: 检查是否已安装MySQL/MariaDB
    print("\n" + "="*60)
    print("步骤2: 检查现有数据库")
    print("="*60)
    stdin, stdout, stderr = ssh.exec_command("rpm -qa | grep -E '(mysql|mariadb)' || echo '未安装'")
    existing = stdout.read().decode('utf-8').strip()
    print(existing)

    if 'mysql' in existing.lower() or 'mariadb' in existing.lower():
        print("\n检测到已安装的数据库，是否需要卸载？")
        print("建议：如果是测试环境可以卸载重装，生产环境请谨慎操作")

    # 步骤3: 下载MySQL Yum Repository
    execute_command(ssh,
        "sudo yum remove -y mysql* mariadb* 2>&1 | tail -10",
        "步骤3: 清理旧版本(如果存在)",
        sudo_password=PASSWORD)

    # 步骤4: 添加MySQL官方仓库
    print("\n" + "="*60)
    print("步骤4: 添加MySQL 8.0官方仓库")
    print("="*60)

    # 下载MySQL仓库配置
    execute_command(ssh,
        "sudo yum install -y https://dev.mysql.com/get/mysql80-community-release-el8-9.noarch.rpm",
        "安装MySQL仓库配置",
        sudo_password=PASSWORD)

    # 步骤5: 导入GPG密钥
    execute_command(ssh,
        "sudo rpm --import https://repo.mysql.com/RPM-GPG-KEY-mysql-2023",
        "步骤5: 导入MySQL GPG密钥",
        sudo_password=PASSWORD)

    # 步骤6: 安装MySQL Server
    print("\n" + "="*60)
    print("步骤6: 安装MySQL Server 8.0")
    print("预计需要3-5分钟...")
    print("="*60)

    execute_command(ssh,
        "sudo yum install -y mysql-community-server",
        "正在安装MySQL...",
        sudo_password=PASSWORD)

    # 步骤7: 启动MySQL服务
    execute_command(ssh,
        "sudo systemctl start mysqld",
        "步骤7: 启动MySQL服务",
        sudo_password=PASSWORD)

    # 步骤8: 设置开机自启
    execute_command(ssh,
        "sudo systemctl enable mysqld",
        "步骤8: 设置MySQL开机自启",
        sudo_password=PASSWORD)

    # 步骤9: 检查MySQL状态
    execute_command(ssh,
        "sudo systemctl status mysqld | head -15",
        "步骤9: 检查MySQL运行状态",
        sudo_password=PASSWORD)

    # 步骤10: 获取临时root密码
    print("\n" + "="*60)
    print("步骤10: 获取MySQL临时root密码")
    print("="*60)
    stdin, stdout, stderr = ssh.exec_command(f"echo '{PASSWORD}' | sudo -S grep 'temporary password' /var/log/mysqld.log | tail -1", get_pty=True)
    temp_password_line = stdout.read().decode('utf-8').strip()
    print(temp_password_line)

    # 提取临时密码
    if 'temporary password' in temp_password_line:
        temp_password = temp_password_line.split('root@localhost: ')[-1].strip()
        print(f"\n临时root密码: {temp_password}")

        # 步骤11: 修改root密码
        print("\n" + "="*60)
        print("步骤11: 修改MySQL root密码")
        print("="*60)

        new_password = "TopN@MySQL2024"

        # 创建SQL脚本来修改密码
        sql_commands = f"""
ALTER USER 'root'@'localhost' IDENTIFIED BY '{new_password}';
FLUSH PRIVILEGES;
"""

        # 上传SQL脚本
        stdin, stdout, stderr = ssh.exec_command("cat > /tmp/change_mysql_password.sql")
        stdin.write(sql_commands)
        stdin.channel.shutdown_write()
        stdout.read()

        # 执行密码修改
        stdin, stdout, stderr = ssh.exec_command(
            f"mysql -uroot -p'{temp_password}' --connect-expired-password < /tmp/change_mysql_password.sql 2>&1"
        )
        result = stdout.read().decode('utf-8')

        if 'ERROR' not in result:
            print(f"✓ root密码已修改为: {new_password}")

            # 步骤12: 测试新密码
            print("\n" + "="*60)
            print("步骤12: 测试MySQL连接")
            print("="*60)
            stdin, stdout, stderr = ssh.exec_command(f"mysql -uroot -p'{new_password}' -e 'SELECT VERSION();' 2>&1")
            version_output = stdout.read().decode('utf-8')
            print(version_output)

            # 步骤13: 创建远程访问用户
            print("\n" + "="*60)
            print("步骤13: 创建远程访问用户")
            print("="*60)

            remote_sql = f"""
CREATE USER 'admin'@'%' IDENTIFIED BY '{new_password}';
GRANT ALL PRIVILEGES ON *.* TO 'admin'@'%' WITH GRANT OPTION;
FLUSH PRIVILEGES;
"""
            stdin, stdout, stderr = ssh.exec_command("cat > /tmp/create_remote_user.sql")
            stdin.write(remote_sql)
            stdin.channel.shutdown_write()
            stdout.read()

            stdin, stdout, stderr = ssh.exec_command(
                f"mysql -uroot -p'{new_password}' < /tmp/create_remote_user.sql 2>&1"
            )
            result = stdout.read().decode('utf-8')

            if 'ERROR' not in result:
                print("✓ 已创建远程访问用户: admin")

            # 步骤14: 配置防火墙
            print("\n" + "="*60)
            print("步骤14: 配置防火墙(开放3306端口)")
            print("="*60)

            execute_command(ssh,
                "sudo firewall-cmd --permanent --add-port=3306/tcp",
                "添加防火墙规则",
                sudo_password=PASSWORD)

            execute_command(ssh,
                "sudo firewall-cmd --reload",
                "重载防火墙配置",
                sudo_password=PASSWORD)

            # 清理临时文件
            execute_command(ssh,
                "rm -f /tmp/change_mysql_password.sql /tmp/create_remote_user.sql",
                "清理临时文件",
                show_output=False)

            # 最终总结
            print("\n" + "="*60)
            print("✓✓✓ MySQL 8.0 安装完成! ✓✓✓")
            print("="*60)
            print("\n数据库信息:")
            print(f"  服务器地址: {SERVER}")
            print(f"  端口: 3306")
            print(f"  root密码: {new_password}")
            print(f"  远程访问用户: admin")
            print(f"  远程访问密码: {new_password}")
            print("\n连接命令:")
            print(f"  本地连接: mysql -uroot -p'{new_password}'")
            print(f"  远程连接: mysql -h {SERVER} -uadmin -p'{new_password}'")
            print("\n管理命令:")
            print("  查看状态: sudo systemctl status mysqld")
            print("  启动服务: sudo systemctl start mysqld")
            print("  停止服务: sudo systemctl stop mysqld")
            print("  重启服务: sudo systemctl restart mysqld")
        else:
            print(f"✗ 密码修改失败: {result}")
    else:
        print("✗ 未找到临时密码，请手动检查")

except Exception as e:
    print(f"\n错误: {e}")
    import traceback
    traceback.print_exc()
finally:
    ssh.close()
