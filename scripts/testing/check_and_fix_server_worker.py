#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查并修复服务器上的RQ Worker问题
"""
import paramiko
import sys
import time

SERVER_HOST = '39.105.12.124'
SERVER_USER = 'u_topn'
SERVER_PATH = '/home/u_topn/TOP_N'

def run_ssh_command(ssh, command, description=""):
    """执行SSH命令并返回结果"""
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
    print("服务器RQ Worker诊断和修复脚本")
    print("=" * 70)

    # 连接服务器
    print(f"\n[连接服务器] {SERVER_USER}@{SERVER_HOST}")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # 尝试使用密钥连接
        ssh.connect(SERVER_HOST, username=SERVER_USER, timeout=10)
        print("✅ SSH连接成功")
    except Exception as e:
        print(f"❌ SSH连接失败: {e}")
        return

    try:
        # 1. 检查Redis服务
        output, error, code = run_ssh_command(
            ssh,
            "redis-cli ping",
            "检查Redis服务"
        )
        if "PONG" in output:
            print("✅ Redis运行正常")
        else:
            print("❌ Redis未运行，尝试启动...")
            run_ssh_command(ssh, "sudo systemctl start redis")

        # 2. 检查Python环境和依赖
        run_ssh_command(
            ssh,
            f"cd {SERVER_PATH} && python3 -c 'import redis, rq; print(\"redis:\", redis.__version__, \"rq:\", rq.__version__)'",
            "检查Python依赖"
        )

        # 3. 检查RQ Worker进程
        output, error, code = run_ssh_command(
            ssh,
            "ps aux | grep 'rq worker' | grep -v grep",
            "检查Worker进程"
        )

        worker_count = len([line for line in output.split('\n') if 'rq worker' in line])
        print(f"\n当前运行的Worker数量: {worker_count}")

        # 4. 检查Redis队列
        output, error, code = run_ssh_command(
            ssh,
            f"""cd {SERVER_PATH} && python3 << 'PYEOF'
import redis
from rq import Queue, Worker

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=False)

# 检查队列
print("\\n=== 队列状态 ===")
for queue_name in ['default', 'user:1', 'user:2']:
    try:
        q = Queue(queue_name, connection=r)
        print(f"  {queue_name}: {len(q)} 个任务")
    except Exception as e:
        print(f"  {queue_name}: 错误 - {e}")

# 检查Worker
print("\\n=== Worker状态 ===")
workers = Worker.all(connection=r)
if workers:
    for w in workers:
        print(f"  {w.name}: {w.state}")
else:
    print("  没有运行的Worker")
PYEOF
""",
            "检查队列和Worker状态"
        )

        # 5. 检查数据库任务状态
        output, error, code = run_ssh_command(
            ssh,
            f"""cd {SERVER_PATH}/backend && python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')
from models import PublishTask, get_db_session

db = get_db_session()
try:
    total = db.query(PublishTask).count()
    queued = db.query(PublishTask).filter(PublishTask.status == 'queued').count()
    running = db.query(PublishTask).filter(PublishTask.status == 'running').count()

    print(f"\\n=== 数据库任务状态 ===")
    print(f"  总任务: {total}")
    print(f"  queued: {queued}")
    print(f"  running: {running}")

    if queued > 0:
        print(f"\\n  最近的queued任务:")
        tasks = db.query(PublishTask).filter(
            PublishTask.status == 'queued'
        ).order_by(PublishTask.created_at.desc()).limit(3).all()

        for t in tasks:
            print(f"    [{t.task_id[:8]}] {t.article_title[:30]} - {t.created_at}")
finally:
    db.close()
PYEOF
""",
            "检查数据库任务"
        )

        # 6. 如果Worker数量不足，启动Worker
        if worker_count < 1:
            print("\n" + "=" * 70)
            print("⚠️  检测到Worker未运行，准备启动...")
            print("=" * 70)

            # 停止旧的worker
            run_ssh_command(
                ssh,
                "pkill -f 'rq worker'",
                "停止旧的Worker进程"
            )
            time.sleep(2)

            # 启动新的worker
            run_ssh_command(
                ssh,
                f"cd {SERVER_PATH} && bash backend/start_workers.sh",
                "启动RQ Workers"
            )

            time.sleep(3)

            # 再次检查
            output, error, code = run_ssh_command(
                ssh,
                "ps aux | grep 'rq worker' | grep -v grep",
                "确认Worker启动"
            )

            worker_count_after = len([line for line in output.split('\n') if 'rq worker' in line])
            print(f"\n启动后的Worker数量: {worker_count_after}")

        # 7. 检查日志
        print("\n" + "=" * 70)
        print("最近的Worker日志 (最后20行)")
        print("=" * 70)
        run_ssh_command(
            ssh,
            f"tail -20 {SERVER_PATH}/logs/worker-1.log 2>/dev/null || echo '日志文件不存在'",
            ""
        )

        # 8. 总结
        print("\n" + "=" * 70)
        print("诊断总结")
        print("=" * 70)
        print("\n下一步操作建议:")
        print("1. 如果Worker已启动，尝试创建一个测试任务")
        print("2. 观察Worker日志: ssh u_topn@39.105.12.124 'tail -f /home/u_topn/TOP_N/logs/worker-1.log'")
        print("3. 检查应用日志: ssh u_topn@39.105.12.124 'tail -f /home/u_topn/TOP_N/logs/app.log'")

    finally:
        ssh.close()
        print("\n连接已关闭")

if __name__ == '__main__':
    main()
