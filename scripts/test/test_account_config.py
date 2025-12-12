#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试账号配置功能
"""
import requests
import json

BASE_URL = 'http://localhost:8080'

def test_add_account():
    """测试添加账号"""
    print("\n1. 测试添加账号...")
    data = {
        'platform': '知乎',
        'username': 'test_user',
        'password': 'test_password',
        'notes': '测试账号'
    }

    response = requests.post(f'{BASE_URL}/api/accounts', json=data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")

def test_get_accounts():
    """测试获取所有账号"""
    print("\n2. 测试获取所有账号...")
    response = requests.get(f'{BASE_URL}/api/accounts')
    print(f"状态码: {response.status_code}")
    data = response.json()
    print(f"账号数量: {len(data.get('accounts', []))}")
    for acc in data.get('accounts', []):
        print(f"  - {acc['platform']}: {acc['username']}")

def test_import_accounts():
    """测试批量导入账号"""
    print("\n3. 测试批量导入账号...")
    with open('示例账号导入.csv', 'rb') as f:
        files = {'file': ('accounts.csv', f, 'text/csv')}
        response = requests.post(f'{BASE_URL}/api/accounts/import', files=files)

    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")

def test_delete_account():
    """测试删除账号"""
    print("\n4. 测试删除账号...")

    # 先获取账号列表
    response = requests.get(f'{BASE_URL}/api/accounts')
    accounts = response.json().get('accounts', [])

    if accounts:
        account_id = accounts[0]['id']
        print(f"删除账号 ID: {account_id}")

        response = requests.delete(f'{BASE_URL}/api/accounts/{account_id}')
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
    else:
        print("没有可删除的账号")

if __name__ == '__main__':
    print("="*80)
    print("账号配置功能测试")
    print("="*80)

    try:
        # 测试健康检查
        response = requests.get(f'{BASE_URL}/api/health')
        if response.status_code == 200:
            print("✓ 服务器运行正常")
        else:
            print("✗ 服务器未响应")
            exit(1)

        # 运行测试
        test_add_account()
        test_get_accounts()
        test_import_accounts()
        test_get_accounts()
        test_delete_account()
        test_get_accounts()

        print("\n" + "="*80)
        print("测试完成!")
        print("="*80)

    except requests.exceptions.ConnectionError:
        print("\n错误: 无法连接到服务器，请确保应用正在运行")
        print("运行命令: cd backend && python app_with_upload.py")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
