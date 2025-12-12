#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查登录验证逻辑
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
        print("🔍 检查登录验证逻辑")
        print("="*80)

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("✓ SSH连接成功\n")

        # 检查 test_zhihu_login 方法中的验证逻辑
        print("[检查登录成功的验证逻辑]")
        cmd = """
cd /home/u_topn/TOP_N/backend
echo "查找登录成功的判断条件:"
grep -A 20 "def test_zhihu_login" login_tester_ultimate.py | grep -A 15 "登录按钮已点击"
"""
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        output = stdout.read().decode('utf-8')
        print(output)

        # 查看最近一次登录的详细日志
        print("\n" + "="*80)
        print("[查看最近登录的详细判断逻辑]")
        cmd = "sudo journalctl -u topn -n 200 --no-pager | grep -A 5 -B 5 '登录失败\\|登录成功\\|check.*login\\|验证登录' | tail -50"
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        output = stdout.read().decode('utf-8')
        if output.strip():
            print(output)
        else:
            print("未找到验证相关日志")

        print("\n" + "="*80)
        print("分析:")
        print("="*80)
        print("""
从日志看，登录流程已成功执行:
1. ✅ DrissionPage 初始化成功
2. ✅ 切换密码登录模式成功
3. ✅ 用户名和密码输入成功
4. ✅ 登录按钮点击成功

但最终结果是"登录失败"，可能原因:
1. 知乎要求验证码/滑块验证
2. 账号密码不正确
3. 登录成功的验证条件未满足（未检测到登录成功的特征）

建议:
1. 使用正确的账号密码测试
2. 如果知乎要求验证码，需要手动处理或使用 Cookie 登录方式
3. 检查登录成功的验证逻辑是否需要调整
""")

        ssh.close()
        return True

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()
