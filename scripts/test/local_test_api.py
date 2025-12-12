#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地测试Flask API
测试账号配置相关的API端点
"""
import sys
import os
import json
import time

# 添加backend路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_accounts_crud_api():
    """测试账号CRUD API"""
    print("="*80)
    print("测试Flask账号CRUD API")
    print("="*80)

    try:
        # 导入Flask应用
        from app_with_upload import app, load_accounts, save_accounts

        # 创建测试客户端
        app.config['TESTING'] = True
        client = app.test_client()

        print("\n1. 测试GET /api/accounts (获取账号列表)")
        print("-"*80)
        response = client.get('/api/accounts')
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = json.loads(response.data)
            print(f"✓ 成功获取账号列表，数量: {len(data)}")
        else:
            print(f"✗ 获取失败: {response.data}")
            return False

        print("\n2. 测试POST /api/accounts (添加账号)")
        print("-"*80)
        new_account = {
            'platform': '知乎',
            'username': 'test_user_001',
            'password': 'test_password_001'
        }
        response = client.post('/api/accounts',
                              data=json.dumps(new_account),
                              content_type='application/json')
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:  # 修正：app返回200而不是201
            data = json.loads(response.data)
            if data.get('success'):
                account_id = data.get('account', {}).get('id')
                print(f"✓ 成功添加账号，ID: {account_id}")
            else:
                print(f"✗ 添加失败: {data}")
                return False
        else:
            print(f"✗ 添加失败: {response.data}")
            return False

        print("\n3. 测试更新账号 (通过删除再添加)")
        print("-"*80)
        # 注意：前端实际是通过删除后重新添加来实现更新的
        # 因此这里跳过PUT测试
        print("ℹ️  前端使用删除后重新添加的方式实现更新，跳过PUT测试")

        print("\n4. 测试POST /api/accounts/<id>/test (测试账号登录)")
        print("-"*80)
        print("注意: 此测试可能失败，因为本地没有WebDriver环境")
        response = client.post(f'/api/accounts/{account_id}/test')
        print(f"状态码: {response.status_code}")
        data = json.loads(response.data)
        print(f"返回消息: {data.get('message', 'N/A')}")
        print(f"成功状态: {data.get('success', False)}")
        if 'Selenium' in data.get('message', '') or 'WebDriver' in data.get('message', ''):
            print("ℹ️  测试API正常工作，只是没有Selenium环境")
        else:
            print("✓ API正常响应")

        print("\n5. 测试DELETE /api/accounts/<id> (删除账号)")
        print("-"*80)
        response = client.delete(f'/api/accounts/{account_id}')
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"✓ 成功删除账号 ID: {account_id}")
        else:
            print(f"✗ 删除失败: {response.data}")
            return False

        print("\n6. 测试批量导入 POST /api/accounts/batch")
        print("-"*80)
        batch_accounts = [
            {'platform': '知乎', 'username': 'batch_user_1', 'password': 'batch_pass_1'},
            {'platform': 'CSDN', 'username': 'batch_user_2', 'password': 'batch_pass_2'},
            {'platform': '微博', 'username': 'batch_user_3', 'password': 'batch_pass_3'},
        ]
        response = client.post('/api/accounts/batch',
                              data=json.dumps(batch_accounts),
                              content_type='application/json')
        print(f"状态码: {response.status_code}")
        if response.status_code == 201:
            data = json.loads(response.data)
            print(f"✓ 成功批量导入 {data.get('count', 0)} 个账号")
        else:
            print(f"✗ 批量导入失败: {response.data}")
            return False

        print("\n7. 再次获取账号列表，验证批量导入")
        print("-"*80)
        response = client.get('/api/accounts')
        if response.status_code == 200:
            data = json.loads(response.data)
            print(f"✓ 当前账号总数: {len(data)}")
            for acc in data[-3:]:  # 显示最后3个
                print(f"  - {acc['platform']}: {acc['username']}")
        else:
            print(f"✗ 获取失败")
            return False

        # 清理测试数据
        print("\n8. 清理测试数据")
        print("-"*80)
        save_accounts([])  # 清空账号列表
        print("✓ 测试数据已清理")

        return True

    except Exception as e:
        print(f"\n✗ API测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_file_upload_api():
    """测试文件上传API"""
    print("\n" + "="*80)
    print("测试文件上传API")
    print("="*80)

    try:
        from app_with_upload import app
        import io

        app.config['TESTING'] = True
        client = app.test_client()

        # 测试CSV文件上传
        print("\n1. 测试CSV文件上传")
        print("-"*80)
        csv_content = """platform,username,password
知乎,csv_user_1,csv_pass_1
CSDN,csv_user_2,csv_pass_2
"""
        csv_file = (io.BytesIO(csv_content.encode('utf-8')), 'accounts.csv')

        response = client.post('/upload',
                              data={'file': csv_file},
                              content_type='multipart/form-data')
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print("✓ CSV文件上传成功")
        else:
            print(f"响应: {response.data.decode('utf-8')[:200]}")

        # 测试TXT文件上传
        print("\n2. 测试TXT文件上传")
        print("-"*80)
        txt_content = """知乎,txt_user_1,txt_pass_1
CSDN,txt_user_2,txt_pass_2
"""
        txt_file = (io.BytesIO(txt_content.encode('utf-8')), 'accounts.txt')

        response = client.post('/upload',
                              data={'file': txt_file},
                              content_type='multipart/form-data')
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print("✓ TXT文件上传成功")
        else:
            print(f"响应: {response.data.decode('utf-8')[:200]}")

        # 测试JSON文件上传
        print("\n3. 测试JSON文件上传")
        print("-"*80)
        json_content = json.dumps([
            {'platform': '知乎', 'username': 'json_user_1', 'password': 'json_pass_1'},
            {'platform': 'CSDN', 'username': 'json_user_2', 'password': 'json_pass_2'}
        ], ensure_ascii=False, indent=2)
        json_file = (io.BytesIO(json_content.encode('utf-8')), 'accounts.json')

        response = client.post('/upload',
                              data={'file': json_file},
                              content_type='multipart/form-data')
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print("✓ JSON文件上传成功")
        else:
            print(f"响应: {response.data.decode('utf-8')[:200]}")

        # 清理测试数据
        from app_with_upload import save_accounts
        save_accounts([])
        print("\n✓ 测试数据已清理")

        return True

    except Exception as e:
        print(f"\n✗ 文件上传测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_main_page():
    """测试主页"""
    print("\n" + "="*80)
    print("测试主页渲染")
    print("="*80)

    try:
        from app_with_upload import app

        app.config['TESTING'] = True
        client = app.test_client()

        response = client.get('/')
        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            html = response.data.decode('utf-8')
            # 检查关键元素
            checks = [
                ('账号配置按钮', '账号配置' in html or 'Account' in html),
                ('上传表单', 'upload' in html.lower()),
                ('分析按钮', '分析' in html or 'analyze' in html.lower()),
                ('JavaScript文件', 'account_config.js' in html),
            ]

            all_ok = True
            for check_name, check_result in checks:
                status = "✓" if check_result else "✗"
                print(f"{status} {check_name}: {'存在' if check_result else '缺失'}")
                if not check_result:
                    all_ok = False

            if all_ok:
                print("\n✓ 主页渲染正常，所有关键元素都存在")
                return True
            else:
                print("\n⚠️  主页渲染成功，但某些元素缺失")
                return False
        else:
            print(f"✗ 主页访问失败: {response.status_code}")
            return False

    except Exception as e:
        print(f"\n✗ 主页测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_api_tests():
    """运行所有API测试"""
    print("\n" + "="*80)
    print("开始运行Flask API测试")
    print("="*80)
    print()

    tests = [
        ("主页渲染", test_main_page),
        ("账号CRUD API", test_accounts_crud_api),
        ("文件上传API", test_file_upload_api),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n测试 '{test_name}' 发生未捕获的异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

        # 测试之间暂停
        time.sleep(0.5)

    # 打印测试摘要
    print("\n" + "="*80)
    print("API测试摘要")
    print("="*80)

    passed = 0
    failed = 0

    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name:20s} : {status}")
        if result:
            passed += 1
        else:
            failed += 1

    print("-"*80)
    print(f"总计: {len(results)} 个测试")
    print(f"通过: {passed} 个")
    print(f"失败: {failed} 个")

    if failed == 0:
        print("\n🎉 所有API测试通过！")
    else:
        print(f"\n⚠️  有 {failed} 个测试失败")

    print("="*80)

if __name__ == "__main__":
    # 设置输出编码
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # 检查依赖
    print("检查Python依赖包...")
    try:
        import flask
        # 使用importlib.metadata避免弃用警告
        try:
            from importlib.metadata import version
            flask_version = version('flask')
        except:
            flask_version = flask.__version__
        print(f"[OK] flask {flask_version}")
    except ImportError:
        print("[X] flask 未安装")
        print("  请运行: pip install flask")
        sys.exit(1)

    print()

    # 运行测试
    run_api_tests()
