"""
测试清理任务功能
"""
import sys
import os

# 添加项目路径到sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.task_queue_manager import get_task_manager
from models import get_db_session, PublishTask
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_clear_tasks():
    """测试清理任务功能"""

    # 获取任务管理器
    manager = get_task_manager()

    print("\n" + "="*60)
    print("测试清理任务功能")
    print("="*60)

    # 测试用户ID（请根据实际情况修改）
    test_user_id = 1

    # 1. 查看当前任务统计
    db = get_db_session()
    try:
        print("\n1. 当前任务统计:")
        print("-" * 60)

        tasks_by_status = {}
        for status in ['pending', 'queued', 'running', 'success', 'failed', 'cancelled']:
            count = db.query(PublishTask).filter(
                PublishTask.user_id == test_user_id,
                PublishTask.status == status
            ).count()
            tasks_by_status[status] = count
            print(f"  {status}: {count} 个任务")

        total = sum(tasks_by_status.values())
        print(f"  总计: {total} 个任务")

    finally:
        db.close()

    # 2. 测试清理成功的任务
    print("\n2. 测试清理成功的任务:")
    print("-" * 60)

    result = manager.clear_tasks(
        user_id=test_user_id,
        status_filter=['success']
    )

    if result['success']:
        print(f"✓ {result['message']}")
        print(f"  已删除: {result['deleted_count']} 个任务")
        if result['failed_count'] > 0:
            print(f"  失败: {result['failed_count']} 个任务")
            if result.get('errors'):
                print(f"  错误: {result['errors'][:3]}")
    else:
        print(f"✗ 清理失败: {result.get('error')} - {result.get('message')}")

    # 3. 测试清理失败的任务
    print("\n3. 测试清理失败的任务:")
    print("-" * 60)

    result = manager.clear_tasks(
        user_id=test_user_id,
        status_filter=['failed']
    )

    if result['success']:
        print(f"✓ {result['message']}")
        print(f"  已删除: {result['deleted_count']} 个任务")
        if result['failed_count'] > 0:
            print(f"  失败: {result['failed_count']} 个任务")
    else:
        print(f"✗ 清理失败: {result.get('error')} - {result.get('message')}")

    # 4. 验证清理后的任务统计
    db = get_db_session()
    try:
        print("\n4. 清理后任务统计:")
        print("-" * 60)

        tasks_by_status = {}
        for status in ['pending', 'queued', 'running', 'success', 'failed', 'cancelled']:
            count = db.query(PublishTask).filter(
                PublishTask.user_id == test_user_id,
                PublishTask.status == status
            ).count()
            tasks_by_status[status] = count
            print(f"  {status}: {count} 个任务")

        total = sum(tasks_by_status.values())
        print(f"  总计: {total} 个任务")

    finally:
        db.close()

    # 5. 测试清理指定任务ID（可选）
    print("\n5. 测试清理指定任务ID:")
    print("-" * 60)

    # 获取一个已取消的任务
    db = get_db_session()
    try:
        cancelled_task = db.query(PublishTask).filter(
            PublishTask.user_id == test_user_id,
            PublishTask.status == 'cancelled'
        ).first()

        if cancelled_task:
            task_id = cancelled_task.task_id
            print(f"  清理任务: {task_id}")

            result = manager.clear_tasks(
                user_id=test_user_id,
                task_ids=[task_id]
            )

            if result['success']:
                print(f"✓ {result['message']}")
            else:
                print(f"✗ 清理失败: {result.get('error')}")
        else:
            print("  没有找到已取消的任务，跳过测试")
    finally:
        db.close()

    # 6. 测试尝试清理正在运行的任务（应该失败）
    print("\n6. 测试清理正在运行的任务（应该失败）:")
    print("-" * 60)

    db = get_db_session()
    try:
        running_task = db.query(PublishTask).filter(
            PublishTask.user_id == test_user_id,
            PublishTask.status.in_(['pending', 'queued', 'running'])
        ).first()

        if running_task:
            task_id = running_task.task_id
            print(f"  尝试清理任务: {task_id} (状态: {running_task.status})")

            result = manager.clear_tasks(
                user_id=test_user_id,
                task_ids=[task_id]
            )

            if not result['success'] or result['failed_count'] > 0:
                print(f"✓ 正确拒绝清理运行中的任务")
                if result.get('errors'):
                    print(f"  错误信息: {result['errors'][0]}")
            else:
                print(f"✗ 意外成功：不应该允许清理运行中的任务")
        else:
            print("  没有找到运行中的任务，跳过测试")
    finally:
        db.close()

    print("\n" + "="*60)
    print("测试完成！")
    print("="*60 + "\n")


if __name__ == '__main__':
    test_clear_tasks()
