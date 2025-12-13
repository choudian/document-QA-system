"""
操作日志装饰器（占位实现）
用于记录用户操作的最小操作日志
"""
import functools
import logging
from typing import Callable, Any
from fastapi import Request
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


def operation_log(
    operation_type: str,
    description: str = "",
    log_request_body: bool = True,
    log_response_body: bool = False,
):
    """
    操作日志装饰器（占位实现）
    
    用于记录用户操作的最小操作日志，包括密钥更新、配置修改、文件上传/删除、标签变更等
    
    Args:
        operation_type: 操作类型（如：config_update, user_create, file_upload）
        description: 操作描述
        log_request_body: 是否记录请求体
        log_response_body: 是否记录响应体
    
    注意：此功能为占位实现，实际实现需要记录到数据库
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 占位：记录操作日志
            try:
                # 尝试从参数中获取 request 和 current_user
                request = None
                current_user = None
                
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                    elif hasattr(arg, 'id'):  # 可能是 User 对象
                        current_user = arg
                
                for key, value in kwargs.items():
                    if isinstance(value, Request):
                        request = value
                    elif key == 'current_user' and hasattr(value, 'id'):
                        current_user = value
                
                # 占位：记录日志
                log_data = {
                    "operation_type": operation_type,
                    "description": description,
                    "user_id": current_user.id if current_user else None,
                    "tenant_id": current_user.tenant_id if current_user else None,
                    "path": request.url.path if request else None,
                    "method": request.method if request else None,
                }
                
                logger.info(f"操作日志（占位）: {log_data}")
                
                # TODO: 实际实现应该：
                # 1. 创建操作日志记录
                # 2. 保存到数据库（operation_logs 表）
                # 3. 记录请求体（如果 log_request_body=True）
                # 4. 记录响应体（如果 log_response_body=True）
                # 5. 记录操作时间、IP 地址等
                
            except Exception as e:
                logger.error(f"记录操作日志失败: {e}", exc_info=True)
                # 失败不影响主流程
            
            return await func(*args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 占位：记录操作日志（同步函数）
            try:
                # 尝试从参数中获取 request 和 current_user
                request = None
                current_user = None
                
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                    elif hasattr(arg, 'id'):  # 可能是 User 对象
                        current_user = arg
                
                for key, value in kwargs.items():
                    if isinstance(value, Request):
                        request = value
                    elif key == 'current_user' and hasattr(value, 'id'):
                        current_user = value
                
                # 占位：记录日志
                log_data = {
                    "operation_type": operation_type,
                    "description": description,
                    "user_id": current_user.id if current_user else None,
                    "tenant_id": current_user.tenant_id if current_user else None,
                    "path": request.url.path if request else None,
                    "method": request.method if request else None,
                }
                
                logger.info(f"操作日志（占位）: {log_data}")
                
                # TODO: 实际实现应该：
                # 1. 创建操作日志记录
                # 2. 保存到数据库（operation_logs 表）
                # 3. 记录请求体（如果 log_request_body=True）
                # 4. 记录响应体（如果 log_response_body=True）
                # 5. 记录操作时间、IP 地址等
                
            except Exception as e:
                logger.error(f"记录操作日志失败: {e}", exc_info=True)
                # 失败不影响主流程
            
            return func(*args, **kwargs)
        
        # 判断函数是否为协程函数
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x80:  # CO_COROUTINE
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

