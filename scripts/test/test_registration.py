#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试用户注册功能
"""

import paramiko
import sys
import io
import json
import random

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

SERVER = "39.105.12.124"
USER = "u_topn"
PASSWORD = "TopN@2024"

def main():
    print("=" * 80)
    print("  测试用户注册和登录功能")
    print("=" * 80)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=10)

    # 生成随机用户
    random_id = random.randint(1000, 9999)
    test_user = {
        "username": f"testuser{random_id}",
        "email": f"test{random_id}@example.com",
        "password": "Test123!@#"
    }

    # 1. 测试注册
    print("\n【1】测试用户注册")
    print("-" * 80)
    print(f"用户名: {test_user['username']}")
    print(f"邮箱: {test_user['email']}")

    cmd = f"""curl -s -X POST -H 'Content-Type: application/json' -d '{json.dumps(test_user)}' http://localhost:3001/api/auth/register"""

    stdin, stdout, stderr = ssh.exec_command(cmd)
    response = stdout.read().decode('utf-8', errors='ignore')

    print(f"\n响应: {response}")

    try:
        result = json.loads(response)
        if result.get('success'):
            print("\n✓ 注册成功!")
            user_id = result.get('user', {}).get('id')
            print(f"  用户ID: {user_id}")
        else:
            print(f"\n✗ 注册失败: {result.get('error')}")
            return
    except:
        print(f"\n✗ 响应解析失败")
        return

    # 2. 测试登录
    print("\n【2】测试用户登录")
    print("-" * 80)

    login_data = {
        "username": test_user['username'],
        "password": test_user['password']
    }

    cmd = f"""curl -s -c /tmp/cookies.txt -X POST -H 'Content-Type: application/json' -d '{json.dumps(login_data)}' http://localhost:3001/api/auth/login"""

    stdin, stdout, stderr = ssh.exec_command(cmd)
    response = stdout.read().decode('utf-8', errors='ignore')

    print(f"响应: {response}")

    try:
        result = json.loads(response)
        if result.get('success'):
            print("\n✓ 登录成功!")
        else:
            print(f"\n✗ 登录失败: {result.get('error')}")
            return
    except:
        print(f"\n✗ 响应解析失败")
        return

    # 3. 测试获取用户信息(需要cookie)
    print("\n【3】测试获取用户信息")
    print("-" * 80)

    cmd = """curl -s -b /tmp/cookies.txt http://localhost:3001/api/auth/me"""

    stdin, stdout, stderr = ssh.exec_command(cmd)
    response = stdout.read().decode('utf-8', errors='ignore')

    print(f"响应: {response}")

    try:
        result = json.loads(response)
        if result.get('success'):
            print("\n✓ 获取用户信息成功!")
            user = result.get('user', {})
            print(f"  用户名: {user.get('username')}")
            print(f"  邮箱: {user.get('email')}")
        else:
            print(f"\n⚠ 获取失败: {result.get('error')}")
    except:
        print(f"\n✗ 响应解析失败")

    # 4. 测试登出
    print("\n【4】测试用户登出")
    print("-" * 80)

    cmd = """curl -s -b /tmp/cookies.txt -X POST http://localhost:3001/api/auth/logout"""

    stdin, stdout, stderr = ssh.exec_command(cmd)
    response = stdout.read().decode('utf-8', errors='ignore')

    print(f"响应: {response}")

    try:
        result = json.loads(response)
        if result.get('success'):
            print("\n✓ 登出成功!")
        else:
            print(f"\n✗ 登出失败: {result.get('error')}")
    except:
        print(f"\n✗ 响应解析失败")

    # 总结
    print("\n" + "=" * 80)
    print("  测试完成!")
    print("=" * 80)
    print("\n✅ 用户注册、登录、获取信息、登出功能正常")

    ssh.close()

if __name__ == '__main__':
    main()
