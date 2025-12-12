#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查登录失败日志
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
        print("🔍 检查登录失败日志")
        print("="*80)

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("✓ SSH连接成功\n")

        # 查看最近50条日志
        print("[1/3] 查看最近的服务日志...")
        cmd = "sudo journalctl -u topn -n 50 --no-pager"
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        output = stdout.read().decode('utf-8')
        print(output[-3000:])  # 显示最后3000字符

        # 查找错误和异常
        print("\n" + "="*80)
        print("[2/3] 查找错误和异常...")
        cmd = "sudo journalctl -u topn -n 100 --no-pager | grep -i -E 'error|exception|traceback|failed' | tail -30"
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        output = stdout.read().decode('utf-8')
        if output.strip():
            print(output)
        else:
            print("未发现明显错误")

        # 查找登录相关日志
        print("\n" + "="*80)
        print("[3/3] 查找登录相关日志...")
        cmd = "sudo journalctl -u topn -n 100 --no-pager | grep -i -E 'login|test.*account|drission|ultimate' | tail -30"
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        output = stdout.read().decode('utf-8')
        if output.strip():
            print(output)
        else:
            print("未发现登录相关日志")

        print("\n" + "="*80)
        print("✅ 日志检查完成")
        print("="*80)

        ssh.close()
        return True

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()
