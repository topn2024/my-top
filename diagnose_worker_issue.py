"""
诊断Worker问题的脚本
检查Redis、RQ、Worker和任务状态
"""
import sys
import os
import io

# 设置UTF-8编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加backend到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

print("=" * 60)
print("任务队列诊断报告")
print("=" * 60)

# 1. 检查Redis依赖
print("\n[1] 检查Redis依赖...")
try:
    import redis
    print("✅ redis模块已安装")
    redis_version = redis.__version__
    print(f"   版本: {redis_version}")
except ImportError as e:
    print("❌ redis模块未安装")
    print(f"   错误: {e}")
    print("   解决: pip install redis")

# 2. 检查RQ依赖
print("\n[2] 检查RQ依赖...")
try:
    import rq
    print("✅ rq模块已安装")
    rq_version = rq.__version__
    print(f"   版本: {rq_version}")
except ImportError as e:
    print("❌ rq模块未安装")
    print(f"   错误: {e}")
    print("   解决: pip install rq")

# 3. 检查Redis连接
print("\n[3] 检查Redis连接...")
try:
    import redis
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=False)
    r.ping()
    print("✅ Redis连接成功")

    # 显示Redis信息
    info = r.info('server')
    print(f"   Redis版本: {info.get('redis_version', 'Unknown')}")
    print(f"   运行时间: {info.get('uptime_in_seconds', 0)} 秒")

except Exception as e:
    print("❌ Redis连接失败")
    print(f"   错误: {e}")
    print("   解决: 请启动Redis服务")
    print("   Windows: 下载并运行 redis-server.exe")
    print("   Linux: sudo systemctl start redis")

# 4. 检查RQ队列
print("\n[4] 检查RQ队列...")
try:
    import redis
    from rq import Queue

    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=False)

    # 检查默认队列
    default_queue = Queue('default', connection=r)
    print(f"✅ 默认队列: {len(default_queue)} 个任务")

    # 检查所有队列
    all_keys = r.keys('rq:queue:*')
    if all_keys:
        print(f"\n   所有队列:")
        for key in all_keys:
            queue_name = key.decode().replace('rq:queue:', '')
            queue = Queue(queue_name, connection=r)
            print(f"   - {queue_name}: {len(queue)} 个任务")
    else:
        print("   ⚠️  没有找到任何队列")

except Exception as e:
    print(f"❌ 检查队列失败: {e}")

# 5. 检查Worker进程
print("\n[5] 检查Worker进程...")
try:
    from rq import Worker
    import redis

    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=False)
    workers = Worker.all(connection=r)

    if workers:
        print(f"✅ 找到 {len(workers)} 个Worker")
        for worker in workers:
            print(f"   - {worker.name}: {worker.state}")
    else:
        print("❌ 没有运行的Worker")
        print("   解决: 需要启动RQ Worker")
        print("   命令: python -m rq worker default --url redis://localhost:6379/0")

except Exception as e:
    print(f"❌ 检查Worker失败: {e}")

# 6. 检查数据库任务
print("\n[6] 检查数据库任务...")
try:
    from models import PublishTask, get_db_session

    db = get_db_session()

    # 统计各状态任务数
    total = db.query(PublishTask).count()
    pending = db.query(PublishTask).filter(PublishTask.status == 'pending').count()
    queued = db.query(PublishTask).filter(PublishTask.status == 'queued').count()
    running = db.query(PublishTask).filter(PublishTask.status == 'running').count()
    success = db.query(PublishTask).filter(PublishTask.status == 'success').count()
    failed = db.query(PublishTask).filter(PublishTask.status == 'failed').count()

    print(f"✅ 数据库连接成功")
    print(f"   总任务数: {total}")
    print(f"   - pending: {pending}")
    print(f"   - queued: {queued} ⚠️ 这些任务在等待Worker处理")
    print(f"   - running: {running}")
    print(f"   - success: {success}")
    print(f"   - failed: {failed}")

    # 显示最近的queued任务
    if queued > 0:
        print(f"\n   最近的queued任务:")
        recent_queued = db.query(PublishTask).filter(
            PublishTask.status == 'queued'
        ).order_by(PublishTask.created_at.desc()).limit(3).all()

        for task in recent_queued:
            print(f"   - [{task.task_id[:8]}...] {task.article_title[:30]}")
            print(f"     创建时间: {task.created_at}")

    db.close()

except Exception as e:
    print(f"❌ 检查数据库失败: {e}")
    import traceback
    traceback.print_exc()

# 7. 问题诊断总结
print("\n" + "=" * 60)
print("诊断总结")
print("=" * 60)

print("\n如果任务停留在 'queued' 状态，最可能的原因是:")
print("❌ RQ Worker 没有运行")
print("\n解决方案:")
print("1. 安装依赖: pip install redis rq")
print("2. 启动Redis: redis-server (或在Windows上运行redis-server.exe)")
print("3. 启动Worker: python -m rq worker default user:* --url redis://localhost:6379/0")
print("\n或者使用项目的启动脚本:")
print("   bash backend/start_workers.sh")

print("\n" + "=" * 60)
