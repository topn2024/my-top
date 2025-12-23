#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署增强版Worker到服务器
"""
import paramiko
import sys
import os

SERVER_HOST = '39.105.12.124'
SERVER_USER = 'u_topn'
SERVER_PATH = '/home/u_topn/TOP_N'

def run_ssh_command(ssh, command, description=""):
    """执行SSH命令"""
    if description:
        print(f"\n[{description}]")
    print(f"$ {command}")

    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    exit_code = stdout.channel.recv_exit_status()

    if output:
        print(output)
    if error and exit_code != 0:
        print(f"错误: {error}")

    return output, error, exit_code

def main():
    print("=" * 70)
    print("部署增强版Worker到生产服务器")
    print("=" * 70)

    # 连接服务器
    print(f"\n[1/6] 连接服务器 {SERVER_USER}@{SERVER_HOST}")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(SERVER_HOST, username=SERVER_USER, timeout=10)
        print("✅ SSH连接成功")
    except Exception as e:
        print(f"❌ SSH连接失败: {e}")
        return

    try:
        # 1. 备份原文件
        run_ssh_command(
            ssh,
            f"cd {SERVER_PATH}/backend/services && cp publish_worker.py publish_worker.py.backup_$(date +%Y%m%d_%H%M%S)",
            "2/6 备份原Worker文件"
        )

        # 2. 上传增强版Worker
        print("\n[3/6] 上传增强版Worker")
        sftp = ssh.open_sftp()
        local_file = 'backend/services/publish_worker_enhanced.py'
        remote_file = f'{SERVER_PATH}/backend/services/publish_worker_enhanced.py'

        try:
            sftp.put(local_file, remote_file)
            print(f"✅ 已上传: {local_file} -> {remote_file}")
        except Exception as e:
            print(f"❌ 上传失败: {e}")
            return
        finally:
            sftp.close()

        # 3. 修改task_queue_manager.py使用增强版Worker
        run_ssh_command(
            ssh,
            f"""cd {SERVER_PATH}/backend/services && sed -i 's/from services.publish_worker import/from services.publish_worker_enhanced import/' task_queue_manager.py""",
            "4/6 修改任务队列管理器导入"
        )

        # 4. 验证文件
        output, _, _ = run_ssh_command(
            ssh,
            f"ls -lh {SERVER_PATH}/backend/services/publish_worker*.py",
            "5/6 验证文件"
        )

        # 5. 重启Worker
        run_ssh_command(
            ssh,
            f"bash {SERVER_PATH}/backend/start_workers.sh",
            "6/6 重启Worker"
        )

        print("\n" + "=" * 70)
        print("✅ 部署完成!")
        print("=" * 70)
        print("\n下一步操作:")
        print("1. 查看Worker日志: ssh u_topn@39.105.12.124 'tail -f /home/u_topn/TOP_N/logs/worker-1.log'")
        print("2. 测试发布任务: 访问 http://39.105.12.124:8080 创建测试文章")
        print("3. 监控任务状态: 查看任务监控面板")

    except Exception as e:
        print(f"\n❌ 部署过程出错: {e}")
        import traceback
        traceback.print_exc()

    finally:
        ssh.close()

if __name__ == '__main__':
    main()
