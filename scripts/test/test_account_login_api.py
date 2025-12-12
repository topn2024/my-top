#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试账号登录 API
"""
import paramiko
import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER_HOST = "39.105.12.124"
SERVER_USER = "u_topn"
SERVER_PASSWORD = "TopN@2024"

def main():
    try:
        print("="*80)
        print("🧪 测试账号登录 API")
        print("="*80)

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("✓ SSH连接成功\n")

        # 获取账号列表
        print("[1/3] 获取账号列表...")
        cmd = "curl -s http://127.0.0.1:8080/api/accounts"
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        output = stdout.read().decode('utf-8')

        import json
        try:
            data = json.loads(output)
            accounts = data.get('accounts', [])
            print(f"找到 {len(accounts)} 个账号")
            for acc in accounts:
                print(f"  ID {acc['id']}: {acc['username']} ({acc['platform']}) - 状态: {acc['status']}")
        except:
            print(f"响应: {output[:200]}")

        # 测试第一个账号（假设有账号）
        if accounts:
            test_account_id = accounts[0]['id']
            print(f"\n[2/3] 测试账号 ID {test_account_id}...")

            # 发起测试请求
            cmd = f"curl -s -X POST http://127.0.0.1:8080/api/accounts/{test_account_id}/test"
            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=90)

            # 等待测试完成（可能需要一些时间）
            print("等待测试完成...")
            time.sleep(15)

            output = stdout.read().decode('utf-8')

            try:
                result = json.loads(output)
                print(f"\n测试结果:")
                print(f"  成功: {result.get('success')}")
                print(f"  消息: {result.get('message')}")
                if 'mode' in result:
                    print(f"  使用模式: {result.get('mode')}")
            except:
                print(f"响应: {output[:300]}")

            # 查看最新日志
            print("\n[3/3] 查看测试日志...")
            cmd = "sudo journalctl -u topn -n 30 --no-pager | grep -i -E 'login|tester|driver|chrome'"
            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
            output = stdout.read().decode('utf-8')
            if output.strip():
                print(output[-2000:])
            else:
                print("未找到相关日志")

        else:
            print("\n未找到账号，跳过测试")

        print("\n" + "="*80)
        print("✅ 测试完成")
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
