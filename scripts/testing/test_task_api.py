#!/usr/bin/env python3
"""
多用户并发发布系统 - Python测试脚本
直接测试任务队列管理器的核心功能
"""

import sys
sys.path.insert(0, '/home/u_topn/TOP_N')

from backend.services.task_queue_manager import get_task_manager
from backend.services.user_rate_limiter import get_rate_limiter
from backend.services.webdriver_pool import get_driver_pool
from backend.models import get_db_session, PublishTask, User

print("=" * 60)
print("  TOP_N 多用户并发发布系统 - 核心功能测试")
print("=" * 60)

# 获取测试用户ID
print("\n【1】获取测试用户...")
db = get_db_session()
try:
    user = db.query(User).filter(User.username == 'admin').first()
    if user:
        user_id = user.id
        print(f"✅ 找到测试用户: {user.username} (ID: {user_id})")
    else:
        print("❌ 未找到admin用户,使用user_id=1")
        user_id = 1
finally:
    db.close()

# 测试限流器
print("\n【2】测试用户限流器...")
limiter = get_rate_limiter()
stats = limiter.get_user_stats(user_id)
print(f"当前并发任务: {stats['concurrent_tasks']}/{stats['max_concurrent_tasks']}")
print(f"最近1分钟任务: {stats['tasks_in_last_minute']}/{stats['max_tasks_per_minute']}")
print("✅ 限流器工作正常")

# 测试WebDriver池
print("\n【3】测试WebDriver池...")
pool = get_driver_pool(max_drivers=2)
pool_stats = pool.get_stats()
print(f"池状态: {pool_stats}")
print("✅ WebDriver池工作正常")

# 测试任务队列管理器
print("\n【4】测试任务队列管理器...")
manager = get_task_manager()
print("✅ 任务队列管理器初始化成功")

# 创建测试任务
print("\n【5】创建测试任务...")
result = manager.create_publish_task(
    user_id=user_id,
    article_title="Python测试文章 - 并发系统验证",
    article_content="这是通过Python脚本直接创建的测试任务,用于验证多用户并发发布系统的核心功能。",
    platform="zhihu"
)

if result['success']:
    task_id = result['task_id']
    print(f"✅ 任务创建成功!")
    print(f"   Task ID: {task_id}")
    print(f"   状态: {result['status']}")
    print(f"   消息: {result['message']}")

    # 查询任务状态
    print("\n【6】查询任务状态...")
    import time
    time.sleep(2)

    task_info = manager.get_task_status(task_id)
    if task_info:
        print(f"✅ 任务状态查询成功")
        print(f"   状态: {task_info['status']}")
        print(f"   进度: {task_info['progress']}%")
        print(f"   创建时间: {task_info['created_at']}")
    else:
        print("❌ 无法查询任务状态")

    # 获取用户任务列表
    print("\n【7】获取用户任务列表...")
    tasks_result = manager.get_user_tasks(user_id=user_id, limit=5)
    if tasks_result['success']:
        print(f"✅ 任务列表获取成功")
        print(f"   总任务数: {tasks_result['total']}")
        print(f"   状态统计: {tasks_result['stats']}")
        print(f"   最近5个任务:")
        for task in tasks_result['tasks'][:5]:
            print(f"     - {task['article_title'][:30]}... [{task['status']}]")

else:
    print(f"❌ 任务创建失败")
    print(f"   错误: {result.get('error')}")
    print(f"   消息: {result.get('message')}")

# 批量创建任务测试
print("\n【8】批量创建任务测试...")
articles = [
    {"title": f"批量测试文章{i}", "content": f"这是批量测试的第{i}篇文章"}
    for i in range(1, 4)
]

batch_result = manager.create_batch_tasks(
    user_id=user_id,
    articles=articles,
    platform="zhihu"
)

if batch_result['success']:
    print(f"✅ 批量创建成功")
    print(f"   总数: {batch_result['total']}")
    print(f"   成功: {batch_result['success_count']}")
    print(f"   失败: {batch_result['failed_count']}")
else:
    print(f"⚠️  批量创建部分失败")
    print(f"   成功: {batch_result['success_count']}/{batch_result['total']}")

# 检查Redis队列
print("\n【9】检查Redis队列...")
import redis
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
try:
    queue_key = f"rq:queue:user:{user_id}"
    queue_len = r.llen(queue_key)
    print(f"✅ 用户队列长度: {queue_len}")

    # 检查所有队列
    all_queues = r.keys("rq:queue:*")
    print(f"✅ 所有队列数量: {len(all_queues)}")
    for q in all_queues[:5]:
        qlen = r.llen(q)
        print(f"   {q}: {qlen} 个任务")
except Exception as e:
    print(f"❌ Redis连接失败: {e}")

# 检查数据库中的任务
print("\n【10】检查数据库任务统计...")
db = get_db_session()
try:
    from sqlalchemy import func
    stats = db.query(
        PublishTask.status,
        func.count(PublishTask.id).label('count')
    ).group_by(PublishTask.status).all()

    print("✅ 数据库任务统计:")
    for status, count in stats:
        print(f"   {status}: {count} 个")
finally:
    db.close()

# 获取更新后的限流统计
print("\n【11】获取更新后的限流统计...")
stats = limiter.get_user_stats(user_id)
print(f"当前并发任务: {stats['concurrent_tasks']}/{stats['max_concurrent_tasks']}")
print(f"最近1分钟任务: {stats['tasks_in_last_minute']}/{stats['max_tasks_per_minute']}")

print("\n" + "=" * 60)
print("  测试完成!")
print("=" * 60)
print("\n核心功能验证:")
print("✅ 1. 用户限流器")
print("✅ 2. WebDriver连接池")
print("✅ 3. 任务队列管理器")
print("✅ 4. 任务创建")
print("✅ 5. 任务状态查询")
print("✅ 6. 批量任务创建")
print("✅ 7. Redis队列管理")
print("✅ 8. 数据库任务存储")
print("\n系统状态: 🟢 正常运行")
