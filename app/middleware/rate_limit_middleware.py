"""
限流中间件（占位实现）
"""
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastapi import status
from app.core.rate_limit import rate_limiter

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    限流中间件（占位实现）
    
    注意：此实现为占位实现，实际生产环境应使用 Redis 等分布式缓存
    """
    
    # 排除的路径（不需要限流）
    EXCLUDED_PATHS = [
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/docs",
        "/openapi.json",
        "/redoc",
    ]
    
    # 默认限流配置（占位）
    DEFAULT_MAX_REQUESTS = 100  # 每分钟最大请求数
    DEFAULT_WINDOW_SECONDS = 60  # 时间窗口（秒）
    
    async def dispatch(self, request: Request, call_next):
        # 检查是否在排除列表中
        if any(request.url.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return await call_next(request)
        
        # 生成限流键（基于 IP 地址，占位）
        client_ip = request.client.host if request.client else "unknown"
        rate_limit_key = f"ip:{client_ip}"
        
        # 检查速率限制
        allowed, remaining = rate_limiter.check_rate_limit(
            key=rate_limit_key,
            max_requests=self.DEFAULT_MAX_REQUESTS,
            window_seconds=self.DEFAULT_WINDOW_SECONDS,
        )
        
        if not allowed:
            logger.warning(f"速率限制触发: {client_ip} - {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "请求过于频繁，请稍后再试（占位实现）",
                    "retry_after": self.DEFAULT_WINDOW_SECONDS,
                },
                headers={
                    "X-RateLimit-Limit": str(self.DEFAULT_MAX_REQUESTS),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": str(self.DEFAULT_WINDOW_SECONDS),
                },
            )
        
        # 添加限流响应头
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.DEFAULT_MAX_REQUESTS)
        response.headers["X-RateLimit-Remaining"] = str(remaining or 0)
        
        return response

