#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试服务器部署状态
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

def execute_command(ssh, command):
    """执行 SSH 命令"""
    print(f"\n执行: {command}")
    print("-" * 60)
    stdin, stdout, stderr = ssh.exec_command(command, timeout=30)

    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')

    if output:
        print(output)
    if error and "sudo" not in error.lower():
        print(f"错误: {error}")

    return output, error

def main():
    """主函数"""
    print("=" * 60)
    print("  测试服务器部署状态")
    print("=" * 60)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print(f"\n连接到 {SERVER}...")
        ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=10)
        print("✓ 连接成功\n")

        # 1. 检查服务进程
        print("\n【1】检查 Gunicorn 进程")
        execute_command(ssh, "ps aux | grep gunicorn | grep -v grep")

        # 2. 检查端口监听
        print("\n【2】检查端口监听")
        execute_command(ssh, "ss -tlnp | grep :3001 || netstat -tlnp | grep :3001")

        # 3. 检查项目目录结构
        print("\n【3】检查项目目录结构")
        execute_command(ssh, f"ls -lh {DEPLOY_DIR}/")

        # 4. 检查 backend 目录
        print("\n【4】检查 backend 目录")
        execute_command(ssh, f"ls -lh {DEPLOY_DIR}/backend/")

        # 5. 检查 templates 目录
        print("\n【5】检查 templates 目录")
        execute_command(ssh, f"ls -lh {DEPLOY_DIR}/templates/")

        # 6. 检查日志文件
        print("\n【6】查看最新日志(最后30行)")
        execute_command(ssh, f"tail -30 {DEPLOY_DIR}/logs/gunicorn.log")

        # 7. 测试 API
        print("\n【7】测试 API 健康检查")
        execute_command(ssh, "curl -s http://localhost:3001/api/health")

        # 8. 测试首页
        print("\n【8】测试首页(查看返回码和内容)")
        execute_command(ssh, "curl -v http://localhost:3001/ 2>&1 | head -20")

        # 9. 检查 Python 模块导入
        print("\n【9】测试 Python 模块导入")
        test_import = f"""cd {DEPLOY_DIR} && python3 -c "
import sys
sys.path.insert(0, 'backend')
from app_factory import create_app
app = create_app()
print('✓ 应用创建成功')
print(f'蓝图: {{list(app.blueprints.keys())}}')
" 2>&1"""
        execute_command(ssh, test_import)

        # 10. 重启服务测试
        print("\n【10】重启服务并等待")
        execute_command(ssh, "pkill -f gunicorn; sleep 2")
        execute_command(ssh, f"cd {DEPLOY_DIR} && nohup gunicorn -c backend/gunicorn_config.py 'backend.app_factory:app' > logs/gunicorn.log 2>&1 &")
        execute_command(ssh, "sleep 3")
        execute_command(ssh, "ps aux | grep gunicorn | grep -v grep")

        # 11. 再次测试
        print("\n【11】重启后测试")
        execute_command(ssh, "curl -s http://localhost:3001/api/health")
        execute_command(ssh, "curl -s -o /dev/null -w 'HTTP状态码: %{http_code}' http://localhost:3001/")

        print("\n" + "=" * 60)
        print("  测试完成")
        print("=" * 60)

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == '__main__':
    main()
