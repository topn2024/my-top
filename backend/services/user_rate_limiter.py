"""
用户级别限流器
使用Redis实现用户级别的速率限制和并发控制
"""
import logging
import time
from typing import Optional
import redis

logger = logging.getLogger(__name__)


class UserRateLimiter:
    """用户级别限流器"""

    def __init__(self, redis_client: redis.Redis):
        """
        初始化限流器

        Args:
            redis_client: Redis客户端实例
        """
        self.redis = redis_client

        # 限流参数
        self.max_concurrent_tasks = 10  # 每用户最多10个并发任务
        self.max_tasks_per_minute = 20  # 每用户每分钟最多20个新任务
        self.window_size = 60  # 滑动窗口大小(秒)

        logger.info(f"用户限流器初始化: concurrent={self.max_concurrent_tasks}, rate={self.max_tasks_per_minute}/min")

    def _get_concurrent_key(self, user_id: int) -> str:
        """获取并发任务数的Redis key"""
        return f"ratelimit:user:{user_id}:concurrent"

    def _get_rate_key(self, user_id: int) -> str:
        """获取速率限制的Redis key"""
        return f"ratelimit:user:{user_id}:rate"

    def check_concurrent_limit(self, user_id: int) -> tuple[bool, int]:
        """
        检查用户当前并发任务数是否超限

        Args:
            user_id: 用户ID

        Returns:
            (是否允许, 当前并发数)
        """
        try:
            key = self._get_concurrent_key(user_id)
            current_count = int(self.redis.get(key) or 0)

            allowed = current_count < self.max_concurrent_tasks
            logger.debug(f"用户{user_id}并发检查: {current_count}/{self.max_concurrent_tasks}, 允许={allowed}")

            return allowed, current_count

        except Exception as e:
            logger.error(f"检查并发限制失败: {e}", exc_info=True)
            # 出错时允许通过，避免影响正常业务
            return True, 0

    def check_rate_limit(self, user_id: int) -> tuple[bool, int]:
        """
        检查用户速率限制(滑动窗口算法)

        Args:
            user_id: 用户ID

        Returns:
            (是否允许, 当前窗口内的请求数)
        """
        try:
            key = self._get_rate_key(user_id)
            current_time = time.time()
            window_start = current_time - self.window_size

            # 使用有序集合实现滑动窗口
            # 1. 移除窗口外的旧记录
            self.redis.zremrangebyscore(key, 0, window_start)

            # 2. 统计当前窗口内的请求数
            current_count = self.redis.zcard(key)

            # 3. 检查是否超限
            allowed = current_count < self.max_tasks_per_minute

            logger.debug(f"用户{user_id}速率检查: {current_count}/{self.max_tasks_per_minute}, 允许={allowed}")

            if allowed:
                # 4. 如果允许，添加当前请求到窗口
                self.redis.zadd(key, {str(current_time): current_time})
                # 5. 设置过期时间(窗口大小的2倍，确保清理)
                self.redis.expire(key, self.window_size * 2)

            return allowed, current_count

        except Exception as e:
            logger.error(f"检查速率限制失败: {e}", exc_info=True)
            # 出错时允许通过
            return True, 0

    def acquire(self, user_id: int) -> bool:
        """
        获取令牌(检查所有限制)

        Args:
            user_id: 用户ID

        Returns:
            是否允许执行任务
        """
        # 1. 检查并发限制
        concurrent_allowed, concurrent_count = self.check_concurrent_limit(user_id)
        if not concurrent_allowed:
            logger.warning(f"用户{user_id}超过并发限制: {concurrent_count}/{self.max_concurrent_tasks}")
            return False

        # 2. 检查速率限制
        rate_allowed, rate_count = self.check_rate_limit(user_id)
        if not rate_allowed:
            logger.warning(f"用户{user_id}超过速率限制: {rate_count}/{self.max_tasks_per_minute}")
            return False

        # 3. 增加并发计数
        key = self._get_concurrent_key(user_id)
        self.redis.incr(key)
        # 设置过期时间(1小时)，防止计数器永久存在
        self.redis.expire(key, 3600)

        logger.info(f"用户{user_id}获取令牌成功, 当前并发:{concurrent_count + 1}")
        return True

    def release(self, user_id: int):
        """
        释放令牌(减少并发计数)

        Args:
            user_id: 用户ID
        """
        try:
            key = self._get_concurrent_key(user_id)
            current = int(self.redis.get(key) or 0)

            if current > 0:
                new_count = self.redis.decr(key)
                logger.debug(f"用户{user_id}释放令牌, 当前并发:{new_count}")
            else:
                logger.warning(f"用户{user_id}尝试释放令牌，但计数已为0")

        except Exception as e:
            logger.error(f"释放令牌失败: {e}", exc_info=True)

    def get_user_stats(self, user_id: int) -> dict:
        """
        获取用户限流统计信息

        Args:
            user_id: 用户ID

        Returns:
            统计信息字典
        """
        try:
            concurrent_key = self._get_concurrent_key(user_id)
            rate_key = self._get_rate_key(user_id)

            current_concurrent = int(self.redis.get(concurrent_key) or 0)

            # 清理过期的速率记录
            current_time = time.time()
            window_start = current_time - self.window_size
            self.redis.zremrangebyscore(rate_key, 0, window_start)

            current_rate = self.redis.zcard(rate_key)

            return {
                'user_id': user_id,
                'concurrent_tasks': current_concurrent,
                'max_concurrent_tasks': self.max_concurrent_tasks,
                'tasks_in_last_minute': current_rate,
                'max_tasks_per_minute': self.max_tasks_per_minute,
                'concurrent_available': self.max_concurrent_tasks - current_concurrent,
                'rate_available': self.max_tasks_per_minute - current_rate
            }

        except Exception as e:
            logger.error(f"获取用户统计失败: {e}", exc_info=True)
            return {
                'user_id': user_id,
                'error': str(e)
            }

    def reset_user_limits(self, user_id: int):
        """
        重置用户的所有限制计数器(管理员功能)

        Args:
            user_id: 用户ID
        """
        try:
            concurrent_key = self._get_concurrent_key(user_id)
            rate_key = self._get_rate_key(user_id)

            self.redis.delete(concurrent_key)
            self.redis.delete(rate_key)

            logger.info(f"已重置用户{user_id}的限流计数器")

        except Exception as e:
            logger.error(f"重置用户限制失败: {e}", exc_info=True)

    def get_all_users_stats(self) -> list:
        """
        获取所有用户的限流统计(管理员功能)

        Returns:
            所有用户的统计信息列表
        """
        try:
            # 扫描所有并发key
            pattern = "ratelimit:user:*:concurrent"
            stats_list = []

            for key in self.redis.scan_iter(match=pattern, count=100):
                # 从key中提取user_id
                # key格式: ratelimit:user:123:concurrent
                key_str = key.decode() if isinstance(key, bytes) else key
                parts = key_str.split(':')
                if len(parts) >= 3:
                    user_id = int(parts[2])
                    stats = self.get_user_stats(user_id)
                    stats_list.append(stats)

            return stats_list

        except Exception as e:
            logger.error(f"获取所有用户统计失败: {e}", exc_info=True)
            return []


# 全局限流器实例
_rate_limiter = None
_limiter_lock = None


def get_rate_limiter(redis_client: redis.Redis = None) -> UserRateLimiter:
    """
    获取全局限流器实例(单例模式)

    Args:
        redis_client: Redis客户端

    Returns:
        UserRateLimiter实例
    """
    global _rate_limiter, _limiter_lock

    if redis_client is None:
        # 使用默认Redis连接
        redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )

    if _rate_limiter is None:
        import threading
        if _limiter_lock is None:
            _limiter_lock = threading.Lock()

        with _limiter_lock:
            if _rate_limiter is None:
                _rate_limiter = UserRateLimiter(redis_client)

    return _rate_limiter
