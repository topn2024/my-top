#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查服务日志并诊断账号加载问题
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
        print("🔍 检查服务日志")
        print("="*80)

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("✓ SSH连接成功\n")

        # 检查服务状态
        print("[1/5] 检查服务状态...")
        cmd = "sudo systemctl status topn --no-pager -l"
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        output = stdout.read().decode('utf-8')
        print(output)

        # 检查最近的服务日志
        print("\n[2/5] 查看最近30条服务日志...")
        cmd = "sudo journalctl -u topn -n 30 --no-pager"
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        output = stdout.read().decode('utf-8')
        print(output)

        # 检查实时日志（最近的错误）
        print("\n[3/5] 查找错误日志...")
        cmd = "sudo journalctl -u topn -n 50 --no-pager | grep -i -E 'error|exception|traceback|failed'"
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        output = stdout.read().decode('utf-8')
        if output.strip():
            print(output)
        else:
            print("未发现明显错误")

        # 检查 accounts.json 文件
        print("\n[4/5] 检查 accounts.json 文件...")
        cmd = "ls -lah /home/u_topn/TOP_N/backend/accounts.json 2>&1 && cat /home/u_topn/TOP_N/backend/accounts.json 2>&1"
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        print(output)
        if error:
            print(f"错误: {error}")

        # 测试 /api/accounts 接口
        print("\n[5/5] 测试 /api/accounts 接口...")
        cmd = "curl -s http://127.0.0.1:8080/api/accounts"
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        output = stdout.read().decode('utf-8')
        print(f"接口响应:\n{output[:500]}")

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
