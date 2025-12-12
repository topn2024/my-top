import sys, subprocess
try: import paramiko
except: subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "paramiko"]); import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("39.105.12.124", 22, "u_topn", "TopN@2024", timeout=30)

# 检查源码包
stdin, stdout, stderr = ssh.exec_command("ls -lh /tmp/Python-3.13.1.tgz 2>&1")
print("源码包状态:")
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))

# 尝试解压并查看错误
stdin, stdout, stderr = ssh.exec_command("cd /tmp && tar -xzf Python-3.13.1.tgz 2>&1 && echo 'SUCCESS' || echo 'FAILED'")
print("\n解压测试:")
print(stdout.read().decode('utf-8'))
err = stderr.read().decode('utf-8')
if err:
    print("错误:", err)

ssh.close()
