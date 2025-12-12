#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python SSH 免密操作示例
使用 paramiko 库进行 SSH 连接和文件传输
"""
import os
import sys
import paramiko
from pathlib import Path

# 服务器配置
SERVER_HOST = '39.105.12.124'
SERVER_PORT = 22
SERVER_USER = 'u_topn'
REMOTE_DIR = '/home/u_topn/TOP_N'

# SSH 密钥路径
SSH_KEY_PATH = str(Path.home() / '.ssh' / 'id_rsa')


class SSHClient:
    """SSH 客户端封装类"""

    def __init__(self, hostname=SERVER_HOST, port=SERVER_PORT, username=SERVER_USER, key_path=SSH_KEY_PATH):
        """初始化 SSH 客户端"""
        self.hostname = hostname
        self.port = port
        self.username = username
        self.key_path = key_path
        self.client = None
        self.sftp = None

    def connect(self):
        """建立 SSH 连接"""
        try:
            # 创建 SSH 客户端
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # 加载私钥
            private_key = paramiko.RSAKey.from_private_key_file(self.key_path)

            # 连接服务器
            self.client.connect(
                hostname=self.hostname,
                port=self.port,
                username=self.username,
                pkey=private_key,
                timeout=10
            )

            print(f"[OK] Connected to server: {self.username}@{self.hostname}")
            return True

        except Exception as e:
            print(f"[ERROR] Connection failed: {str(e)}")
            return False

    def execute_command(self, command):
        """执行远程命令"""
        if not self.client:
            print("[ERROR] Not connected to server")
            return None

        try:
            stdin, stdout, stderr = self.client.exec_command(command)
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            exit_code = stdout.channel.recv_exit_status()

            return {
                'output': output,
                'error': error,
                'exit_code': exit_code
            }
        except Exception as e:
            print(f"[ERROR] Command execution failed: {str(e)}")
            return None

    def upload_file(self, local_path, remote_path):
        """上传文件到服务器"""
        try:
            if not self.sftp:
                self.sftp = self.client.open_sftp()

            self.sftp.put(local_path, remote_path)
            print(f"[OK] Uploaded: {local_path} -> {remote_path}")
            return True

        except Exception as e:
            print(f"[ERROR] Upload failed: {str(e)}")
            return False

    def download_file(self, remote_path, local_path):
        """从服务器下载文件"""
        try:
            if not self.sftp:
                self.sftp = self.client.open_sftp()

            self.sftp.get(remote_path, local_path)
            print(f"[OK] Downloaded: {remote_path} -> {local_path}")
            return True

        except Exception as e:
            print(f"[ERROR] Download failed: {str(e)}")
            return False

    def upload_directory(self, local_dir, remote_dir):
        """上传整个目录"""
        try:
            if not self.sftp:
                self.sftp = self.client.open_sftp()

            # 创建远程目录
            try:
                self.sftp.mkdir(remote_dir)
            except:
                pass

            # 递归上传文件
            for root, dirs, files in os.walk(local_dir):
                # 创建子目录
                for dir_name in dirs:
                    local_subdir = os.path.join(root, dir_name)
                    remote_subdir = os.path.join(
                        remote_dir,
                        os.path.relpath(local_subdir, local_dir)
                    ).replace('\\', '/')

                    try:
                        self.sftp.mkdir(remote_subdir)
                    except:
                        pass

                # 上传文件
                for file_name in files:
                    local_file = os.path.join(root, file_name)
                    remote_file = os.path.join(
                        remote_dir,
                        os.path.relpath(local_file, local_dir)
                    ).replace('\\', '/')

                    self.sftp.put(local_file, remote_file)
                    print(f"  [OK] {local_file} -> {remote_file}")

            print(f"[OK] Directory uploaded: {local_dir} -> {remote_dir}")
            return True

        except Exception as e:
            print(f"[ERROR] Directory upload failed: {str(e)}")
            return False

    def close(self):
        """关闭连接"""
        if self.sftp:
            self.sftp.close()
        if self.client:
            self.client.close()
        print("[OK] Connection closed")


def main():
    """主函数 - 示例用法"""
    print("=" * 60)
    print("Python SSH 免密操作示例")
    print("=" * 60)

    # 创建 SSH 客户端
    ssh = SSHClient()

    # 连接服务器
    if not ssh.connect():
        return

    print("\n[示例 1] 执行简单命令")
    result = ssh.execute_command('whoami && hostname && date')
    if result:
        print(result['output'])

    print("\n[示例 2] 查看项目目录")
    result = ssh.execute_command(f'ls -lh {REMOTE_DIR} | head -10')
    if result:
        print(result['output'])

    print("\n[示例 3] 检查 Python 环境")
    result = ssh.execute_command('python3 --version && pip3 --version')
    if result:
        print(result['output'])

    print("\n[示例 4] 检查服务状态")
    result = ssh.execute_command(f'''
        cd {REMOTE_DIR}
        echo "=== Gunicorn 进程 ==="
        ps aux | grep gunicorn | grep -v grep | wc -l

        echo "=== Redis 状态 ==="
        redis-cli ping 2>/dev/null || echo "Redis 未运行"

        echo "=== 磁盘使用 ==="
        df -h | grep -E "Filesystem|/$"
    ''')
    if result:
        print(result['output'])

    # 文件传输示例（注释掉，按需使用）
    # print("\n[示例 5] 上传文件")
    # ssh.upload_file('local_file.txt', f'{REMOTE_DIR}/uploaded_file.txt')

    # print("\n[示例 6] 下载文件")
    # ssh.download_file(f'{REMOTE_DIR}/remote_file.txt', './downloaded_file.txt')

    # print("\n[示例 7] 上传目录")
    # ssh.upload_directory('./local_dir', f'{REMOTE_DIR}/uploaded_dir')

    # 关闭连接
    print("\n" + "=" * 60)
    ssh.close()
    print("=" * 60)


if __name__ == '__main__':
    main()
