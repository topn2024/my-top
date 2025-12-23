#!/usr/bin/env python3
"""测试异步发布功能"""
import sys
import time
sys.path.insert(0, '/home/u_topn/TOP_N/backend')

from services.task_queue_manager import get_task_manager

print("=" * 60)
print("测试异步发布功能")
print("=" * 60)

# 创建任务管理器
task_manager = get_task_manager()

# 创建测试任务
print("\n1. 创建测试任务...")
result = task_manager.create_publish_task(
    user_id=1,
    article_title=f'测试任务 - {int(time.time())}',
    article_content='这是一个测试任务\n\n用于验证异步发布功能是否正常工作。',
    platform='zhihu',
    article_id=None
)

if not result['success']:
    print(f"✗ 创建失败: {result.get('error')}")
    sys.exit(1)

task_id = result['task_id']
print(f"✓ 任务已创建: {task_id}")
print(f"  状态: {result['status']}")

# 监控任务状态
print("\n2. 监控任务执行...")
for i in range(30):
    time.sleep(2)
    status_info = task_manager.get_task_status(task_id)

    if not status_info:
        print(f"  [{i*2}s] 无法获取状态")
        continue

    status = status_info['status']
    progress = status_info.get('progress', 0)

    print(f"  [{i*2}s] 状态: {status}, 进度: {progress}%")

    if status == 'success':
        print(f"\n✓✓ 任务成功!")
        print(f"  文章URL: {status_info.get('result_url')}")
        break
    elif status == 'failed':
        print(f"\n✗ 任务失败!")
        print(f"  错误: {status_info.get('error_message')}")
        break
    elif status in ['queued', 'pending']:
        if i > 15:
            print(f"\n⚠ 任务超过30秒仍未开始执行，可能Worker有问题")
            break

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
