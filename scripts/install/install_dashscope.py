#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安装 dashscope (包含 cryptography 依赖)
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
        print("📦 安装 dashscope 和 cryptography")
        print("="*80)

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
        print("✓ SSH连接成功\n")

        # 安装 dashscope (会自动安装 cryptography 依赖)
        print("[1/2] 安装 dashscope (包含 cryptography)...")
        print("注意: cryptography 约 4.5MB，可能需要较长时间下载")
        print()

        cmd = "pip3 install --user dashscope"
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=600)  # 10分钟超时

        # 实时显示安装进度
        last_output_time = time.time()
        while not stdout.channel.exit_status_ready():
            if stdout.channel.recv_ready():
                data = stdout.channel.recv(1024).decode('utf-8', errors='ignore')
                print(data, end='', flush=True)
                last_output_time = time.time()
            else:
                # 如果超过30秒没有输出，显示等待提示
                if time.time() - last_output_time > 30:
                    print(".", end='', flush=True)
                    last_output_time = time.time()
                time.sleep(1)

        # 读取剩余输出
        remaining = stdout.read().decode('utf-8', errors='ignore')
        if remaining:
            print(remaining)

        print("\n✓ dashscope 安装完成")

        # 验证安装
        print("\n[2/2] 验证安装...")
        test_cmd = """
python3 << 'EOF'
try:
    import cryptography
    print(f"✓ cryptography {cryptography.__version__}")
except Exception as e:
    print(f"✗ cryptography: {e}")

try:
    import dashscope
    print(f"✓ dashscope 已安装")
except Exception as e:
    print(f"✗ dashscope: {e}")
EOF
"""

        stdin, stdout, stderr = ssh.exec_command(test_cmd, timeout=30)
        output = stdout.read().decode('utf-8')
        print(output)

        print("\n" + "="*80)
        print("✅ 安装完成!")
        print("="*80)
        print("\n现在系统支持以下 AI 库:")
        print("  • openai (OpenAI API)")
        print("  • anthropic (Claude API)")
        print("  • dashscope (通义千问 API)")
        print("  • zhipuai (智谱 AI API)")

        ssh.close()
        return True

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()
