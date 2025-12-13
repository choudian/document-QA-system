"""
限流工具类（占位实现）
"""
from typing import Optional, Dict
import time
from collections import defaultdict


class RateLimiter:
    """
    限流器（占位实现）
    
    注意：此实现为占位实现，实际生产环境应使用 Redis 等分布式缓存
    """
    
    def __init__(self):
        # 内存存储（占位），实际应使用 Redis
        self._requests: Dict[str, list] = defaultdict(list)
    
    def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> tuple[bool, Optional[int]]:
        """
        检查是否超过速率限制
        
        Args:
            key: 限流键（如 IP、用户ID、租户ID）
            max_requests: 最大请求数
            window_seconds: 时间窗口（秒）
        
        Returns:
            (是否允许, 剩余请求数)
        """
        now = time.time()
        window_start = now - window_seconds
        
        # 清理过期记录
        requests = self._requests[key]
        requests[:] = [req_time for req_time in requests if req_time > window_start]
        
        # 检查是否超过限制
        if len(requests) >= max_requests:
            return False, 0
        
        # 记录本次请求
        requests.append(now)
        remaining = max_requests - len(requests)
        
        return True, remaining
    
    def reset(self, key: str):
        """重置限流计数"""
        if key in self._requests:
            del self._requests[key]


# 全局限流器实例（占位）
rate_limiter = RateLimiter()

