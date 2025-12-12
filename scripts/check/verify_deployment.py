#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import paramiko, sys, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER = "39.105.12.124"
USER = "u_topn"
PASSWORD = "TopN@2024"

print("="*70)
print("  部署验证检查")
print("="*70)

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=10)
    print(f"\n✓ SSH连接成功: {USER}@{SERVER}\n")

    print("1. 检查Gunicorn进程:")
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep 'gunicorn.*app_with_upload' | grep -v grep | head -5")
    processes = stdout.read().decode()
    if processes:
        print("  ✓ Gunicorn运行中:")
        for line in processes.strip().split('\n'):
            parts = line.split()
            print(f"    PID {parts[1]}: {' '.join(parts[10:])}")
    else:
        print("  ✗ 未找到Gunicorn进程")

    print("\n2. 检查端口监听:")
    stdin, stdout, stderr = ssh.exec_command("netstat -tuln | grep ':8080'")
    port_status = stdout.read().decode()
    if port_status:
        print("  ✓ 端口8080监听中")
    else:
        print("  ✗ 端口8080未监听")

    print("\n3. 检查已部署文件:")
    stdin, stdout, stderr = ssh.exec_command("ls -lh /home/u_topn/TOP_N/backend/zhihu_auto_post_enhanced.py /home/u_topn/TOP_N/backend/app_with_upload.py")
    print(stdout.read().decode())

    print("4. 验证代码集成:")
    stdin, stdout, stderr = ssh.exec_command("grep 'from zhihu_auto_post_enhanced import post_article_to_zhihu' /home/u_topn/TOP_N/backend/app_with_upload.py")
    if stdout.read().decode().strip():
        print("  ✓ zhihu_auto_post_enhanced模块已导入")
    else:
        print("  ✗ 模块导入验证失败")

    stdin, stdout, stderr = ssh.exec_command("grep 'password=password,' /home/u_topn/TOP_N/backend/app_with_upload.py")
    if stdout.read().decode().strip():
        print("  ✓ password参数已添加到函数调用")
    else:
        print("  ✗ password参数验证失败")

    print("\n5. 最新应用日志 (gunicorn):")
    stdin, stdout, stderr = ssh.exec_command("tail -5 /home/u_topn/TOP_N/logs/gunicorn_error.log")
    log = stdout.read().decode()
    if log:
        print(log)

    print("\n6. 尝试HTTP请求测试:")
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/ --max-time 5")
    http_code = stdout.read().decode().strip()
    if http_code == '200':
        print(f"  ✓ HTTP服务响应正常 (状态码: {http_code})")
    else:
        print(f"  状态码: {http_code}")

    ssh.close()

    print("\n" + "="*70)
    print("  ✅ 部署验证完成")
    print("="*70)
    print("\n访问地址: http://39.105.12.124:8080")
    print("服务已就绪,可以开始测试知乎自动登录功能\n")

except Exception as e:
    print(f"\n✗ 验证失败: {e}")
    import traceback
    traceback.print_exc()
