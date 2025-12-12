#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试服务器问题
"""

import paramiko
import sys
import io

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 服务器配置
SERVER = "39.105.12.124"
USER = "u_topn"
PASSWORD = "TopN@2024"
DEPLOY_DIR = "/home/u_topn/TOP_N"

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=10)

    # 获取详细的错误信息
    test_cmd = f"""cd {DEPLOY_DIR} && python3 << 'PYEOF'
import sys
sys.path.insert(0, 'backend')

from app_factory import create_app

app = create_app()

# 打印所有注册的路由
print("注册的路由:")
for rule in app.url_map.iter_rules():
    print("  ", rule.endpoint, " -> ", rule.rule)

# 打印蓝图
print("蓝图:", list(app.blueprints.keys()))

# 测试处理请求
print("测试处理请求:")
with app.test_client() as client:
    resp = client.get('/')
    print("状态码:", resp.status_code)
    print("响应:", resp.data[:200])

PYEOF
"""

    stdin, stdout, stderr = ssh.exec_command(test_cmd)
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')

    print("输出:")
    print(output)
    if error:
        print("\n错误:")
        print(error)

    ssh.close()

if __name__ == '__main__':
    main()
