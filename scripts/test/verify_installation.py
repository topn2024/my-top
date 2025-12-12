import sys, subprocess
try: import paramiko
except: subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "paramiko"]); import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("39.105.12.124", 22, "u_topn", "TopN@2024", timeout=30)

print("="*60)
print("Python 3.14.0 安装验证")
print("="*60)

commands = [
    ("Python 3.14版本", "python3.14 --version"),
    ("Python 3符号链接", "python3 --version"),
    ("Python可执行文件位置", "which python3.14 python3"),
    ("pip版本", "python3.14 -m pip --version"),
    ("已安装的Python版本", "ls -la /usr/local/bin/python3*"),
]

for desc, cmd in commands:
    print(f"\n{desc}:")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    output = stdout.read().decode('utf-8').strip()
    if output:
        for line in output.split('\n'):
            print(f"  {line}")

ssh.close()
print("\n" + "="*60)
print("✓ 验证完成")
print("="*60)
