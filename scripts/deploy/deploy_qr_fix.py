#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署Cookie保存修复版本
"""
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

try:
    print("=" * 80)
    print("部署Cookie保存修复")
    print("=" * 80)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
    print("✓ SSH连接成功\n")

    # 备份当前文件
    print("[1/3] 备份当前文件...")
    cmd = "cp /home/u_topn/TOP_N/backend/qrcode_login.py /home/u_topn/TOP_N/backend/qrcode_login.py.backup_cookie_fix"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    stdout.read()
    print("✓ 备份完成")

    # 上传修复版本
    print("\n[2/3] 上传修复版本...")
    sftp = ssh.open_sftp()
    sftp.put('qrcode_login_fixed.py', '/home/u_topn/TOP_N/backend/qrcode_login.py')
    sftp.close()
    print("✓ 文件已上传")

    # 重启服务
    print("\n[3/3] 重启服务...")
    cmd = "sudo systemctl restart topn"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    stdout.read()

    import time
    time.sleep(4)

    # 检查服务状态
    cmd = "sudo systemctl status topn --no-pager | head -15"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    print(stdout.read().decode('utf-8'))

    print("\n" + "=" * 80)
    print("✅ 修复部署完成!")
    print("=" * 80)
    print("""
修复内容:
1. 添加 cookies_saved 标志,避免重复保存
2. 提前获取Cookie,避免在浏览器关闭后获取
3. 增强close()方法的错误处理,忽略连接断开错误
4. 优化日志输出

现在可以重新测试扫码登录:
1. 访问 http://39.105.12.124:8080
2. 添加知乎账号并测试
3. 扫码登录
4. 应该能正常保存Cookie,没有错误提示
    """)

    ssh.close()

except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
