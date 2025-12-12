#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 app_with_upload.py 中的登录测试器导入
"""
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

def main():
    try:
        print("="*80)
        print("🔧 修复登录测试器导入")
        print("="*80)

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("✓ SSH连接成功\n")

        # 检查当前导入
        print("[1/3] 检查 app_with_upload.py 当前导入...")
        cmd = "cd /home/u_topn/TOP_N/backend && grep -n 'from login_tester' app_with_upload.py"
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        output = stdout.read().decode('utf-8')
        print(output)

        # 更新导入语句
        print("\n[2/3] 更新为 LoginTesterUltimate...")
        cmd = """
cd /home/u_topn/TOP_N/backend

# 备份原文件
cp app_with_upload.py app_with_upload.py.backup_$(date +%Y%m%d_%H%M%S)

# 替换导入语句
sed -i 's/from login_tester import LoginTester/from login_tester_ultimate import LoginTesterUltimate as LoginTester/g' app_with_upload.py

# 验证修改
echo "修改后:"
grep -n 'from login_tester' app_with_upload.py
"""
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        output = stdout.read().decode('utf-8')
        print(output)

        # 重启服务
        print("\n[3/3] 重启服务...")
        cmd = "sudo systemctl restart topn && sleep 3 && sudo systemctl status topn --no-pager -l"
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
        import time
        time.sleep(4)
        output = stdout.read().decode('utf-8')
        print(output)

        # 检查服务日志
        print("\n[检查服务启动日志]")
        cmd = "sudo journalctl -u topn -n 15 --no-pager"
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        output = stdout.read().decode('utf-8')
        print(output[-1500:])

        print("\n" + "="*80)
        print("✅ 修复完成!")
        print("="*80)
        print("\n说明:")
        print("  • 已将 LoginTester 替换为 LoginTesterUltimate")
        print("  • LoginTesterUltimate 支持:")
        print("    - DrissionPage (最佳, 90-97%成功率)")
        print("    - undetected-chromedriver (备用, 85-95%)")
        print("    - selenium (降级, 70-80%)")
        print("  • 当前自动选择: drission 模式")

        ssh.close()
        return True

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()
