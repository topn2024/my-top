#!/usr/bin/env python3
"""
定时任务维护脚本
可以通过cron或systemd timer定期执行

使用方法:
    # 直接执行
    python scheduled_maintenance.py

    # 通过cron每小时执行一次
    0 * * * * cd /home/u_topn/TOP_N/backend && /home/u_topn/TOP_N/venv/bin/python scripts/scheduled_maintenance.py >> /tmp/maintenance.log 2>&1

    # 通过cron每天凌晨2点执行一次
    0 2 * * * cd /home/u_topn/TOP_N/backend && /home/u_topn/TOP_N/venv/bin/python scripts/scheduled_maintenance.py >> /tmp/maintenance.log 2>&1
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """执行定时维护任务"""
    logger.info("=" * 60)
    logger.info(f"定时维护任务开始执行: {datetime.now().isoformat()}")
    logger.info("=" * 60)

    try:
        from services.task_queue_manager import get_task_manager

        manager = get_task_manager()
        result = manager.run_maintenance()

        # 打印结果
        logger.info("维护任务执行结果:")

        if 'results' in result:
            # 同步结果
            sync = result['results'].get('sync', {})
            logger.info(f"  [状态同步] 同步: {sync.get('synced_count', 0)}, 错误: {sync.get('error_count', 0)}")

            # Redis清理结果
            redis = result['results'].get('redis_cleanup', {})
            logger.info(f"  [Redis清理] 失败任务: {redis.get('failed_jobs_cleaned', 0)}, 结果记录: {redis.get('results_cleaned', 0)}")

            # 过期任务清理结果
            expired = result['results'].get('expired_cleanup', {})
            logger.info(f"  [过期清理] 删除: {expired.get('deleted_count', 0)}")

        logger.info("=" * 60)
        logger.info(f"定时维护任务执行完成: {datetime.now().isoformat()}")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"定时维护任务执行失败: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
