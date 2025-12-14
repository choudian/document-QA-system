"""
全局异常拦截中间件
统一捕获和记录所有未处理的异常
"""
import logging
import traceback
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp
from fastapi import status
from app.core.logging_config import log_exception

logger = logging.getLogger(__name__)


class ExceptionMiddleware(BaseHTTPMiddleware):
    """全局异常拦截中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        """
        拦截请求，捕获所有异常
        
        Args:
            request: 请求对象
            call_next: 下一个中间件或路由处理器
        
        Returns:
            响应对象
        """
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            # 记录异常信息
            context = {
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_host": request.client.host if request.client else "unknown",
            }
            
            # 尝试获取用户信息
            try:
                user = getattr(request.state, "user", None)
                if user:
                    context["user_id"] = getattr(user, "id", None)
                    context["username"] = getattr(user, "username", None)
            except:
                pass
            
            # 记录异常
            log_exception(logger, exc, context)
            
            # 返回统一的错误响应
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": f"内部服务器错误: {str(exc)}",
                    "error_type": type(exc).__name__,
                }
            )

