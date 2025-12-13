"""
审计日志中间件
自动记录所有API请求和响应
"""
import time
import json
import asyncio
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse, JSONResponse
from starlette.types import ASGIApp, Message, Receive, Send
from starlette.datastructures import MutableHeaders
from fastapi.responses import JSONResponse as FastAPIJSONResponse
from starlette.responses import Response as StarletteResponse
from fastapi import status
from app.core.database import SessionLocal
from app.core.audit_utils import mask_sensitive_data, serialize_for_storage
from app.core.security import verify_token
from app.core.langfuse_client import _langfuse_client
from app.models.audit_log import AuditLog
import logging

logger = logging.getLogger(__name__)




class ResponseCapture(Response):
    """包装响应对象以捕获响应体"""
    def __init__(self, response: Response, captured_body_ref: list, audit_callback: Callable):
        # 初始化Response，不直接复制headers（因为headers是只读的）
        super().__init__(
            content=b"",  # 空内容，实际内容由原始响应提供
            status_code=response.status_code,
            headers=dict(response.headers),  # 复制headers字典
            media_type=getattr(response, 'media_type', None)
        )
        self._response = response
        self._captured_body_ref = captured_body_ref  # 使用列表引用以便修改
        self._audit_callback = audit_callback  # 审计日志回调函数
        
    async def __call__(self, scope: dict, receive: Receive, send: Send):
        """ASGI调用，拦截响应体"""
        async def send_wrapper(message: Message):
            if message["type"] == "http.response.body":
                body = message.get("body", b"")
                if body:
                    self._captured_body_ref[0] += body
            await send(message)
        
        # 调用原始响应的ASGI接口
        await self._response(scope, receive, send_wrapper)
        
        # 响应发送完成后，调用审计日志回调
        if self._audit_callback:
            await self._audit_callback()


class AuditMiddleware(BaseHTTPMiddleware):
    """审计日志中间件"""
    
    # 排除的路径（不需要记录审计日志）
    EXCLUDED_PATHS = [
        "/",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/favicon.ico",
    ]
    
    # 排除的路径前缀（不需要记录审计日志）
    EXCLUDED_PREFIXES = [
        "/api/v1/audit-logs",  # 审计日志查询接口本身不记录（避免循环）
    ]
    
    # 最大请求/响应体大小（字节），超过则不记录完整内容
    MAX_BODY_SIZE = 100000  # 100KB
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并记录审计日志"""
        
        # 检查是否应该记录此路径
        if self._should_exclude(request.url.path):
            return await call_next(request)
        
        # 记录开始时间
        start_time = time.time()
        
        # 获取客户端信息
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        # 获取用户信息
        user_id, tenant_id = self._get_user_info(request)
        
        # 读取请求体（需要先读取并缓存，因为FastAPI的请求体只能读取一次）
        request_body = await self._read_request_body(request)
        request_size = len(request_body.encode('utf-8')) if request_body else 0
        
        # 读取查询参数
        query_params = dict(request.query_params) if request.query_params else None
        
        # 如果读取了请求体，需要重新设置请求体（因为已经被消费了）
        # 注意：这可能会影响某些路由，但大多数情况下应该没问题
        # 如果遇到问题，可以考虑使用request.stream()来读取
        
        # 调用下一个中间件/路由处理程序
        response_body_str = None
        response_size = 0
        captured_body_list = [b""]  # 使用列表以便在ResponseCapture中修改
        response_status = 200
        response_content_type = ""
        
        try:
            # 调用下一个中间件/路由处理程序
            response = await call_next(request)
            
            # 获取响应状态和内容类型
            response_status = response.status_code
            response_content_type = response.headers.get("content-type", "")
            
            # 定义审计日志回调函数（在响应对象创建后定义，以便访问response_status等变量）
            async def log_audit_after_response():
                """在响应发送后记录审计日志"""
                try:
                    # 计算耗时
                    duration_ms = int((time.time() - start_time) * 1000)
                    
                    # 处理捕获的响应体（从列表中获取）
                    captured_body = captured_body_list[0]
                    response_body_str, response_size = await self._process_captured_body(
                        captured_body, response_content_type
                    )
                    
                    # 始终记录到审计日志表（保持现有行为）
                    await self._log_audit(
                        user_id=user_id,
                        tenant_id=tenant_id,
                        method=request.method,
                        path=request.url.path,
                        query_params=query_params,
                        request_body=request_body,
                        response_status=response_status,
                        response_body=response_body_str,
                        request_size=request_size,
                        response_size=response_size,
                        duration_ms=duration_ms,
                        ip_address=client_ip,
                        user_agent=user_agent,
                    )
                    
                    # 如果 Langfuse 已启用，额外记录到 Langfuse
                    if _langfuse_client.is_enabled():
                        try:
                            # 准备 Langfuse Trace 的元数据
                            langfuse_metadata = {
                                "tenant_id": tenant_id,
                                "method": request.method,
                                "status_code": response_status,
                                "duration_ms": duration_ms,
                                "ip_address": client_ip,
                                "user_agent": user_agent,
                            }
                            
                            # 记录到 Langfuse（异步，失败不影响主流程）
                            trace_id = _langfuse_client.trace(
                                name=request.url.path,
                                user_id=user_id,
                                metadata=langfuse_metadata,
                                input=request_body,  # 已脱敏
                                output=response_body_str,  # 已脱敏
                            )
                            
                            if trace_id:
                                logger.debug(f"Langfuse Trace 已记录: {trace_id}")
                        except Exception as e:
                            logger.warning(f"记录 Langfuse Trace 失败: {e}", exc_info=True)
                            # 失败不影响审计日志记录
                except Exception as e:
                    logger.error(f"记录审计日志失败: {e}", exc_info=True)
            
            # 使用ResponseCapture包装响应以捕获响应体
            wrapped_response = ResponseCapture(response, captured_body_list, log_audit_after_response)
        except Exception as e:
            # 如果发生异常，记录错误响应
            response = Response(
                content=json.dumps({"detail": str(e)}),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                media_type="application/json"
            )
            captured_body_list[0] = json.dumps({"detail": str(e)}).encode('utf-8')
            response_status = status.HTTP_500_INTERNAL_SERVER_ERROR
            response_content_type = "application/json"
            
            # 定义错误响应的审计日志回调
            async def log_error_audit():
                try:
                    duration_ms = int((time.time() - start_time) * 1000)
                    captured_body = captured_body_list[0]
                    response_body_str, response_size = await self._process_captured_body(
                        captured_body, response_content_type
                    )
                    # 始终记录到审计日志表
                    await self._log_audit(
                        user_id=user_id,
                        tenant_id=tenant_id,
                        method=request.method,
                        path=request.url.path,
                        query_params=query_params,
                        request_body=request_body,
                        response_status=response_status,
                        response_body=response_body_str,
                        request_size=request_size,
                        response_size=response_size,
                        duration_ms=duration_ms,
                        ip_address=client_ip,
                        user_agent=user_agent,
                    )
                    
                    # 如果 Langfuse 已启用，额外记录到 Langfuse
                    if _langfuse_client.is_enabled():
                        try:
                            langfuse_metadata = {
                                "tenant_id": tenant_id,
                                "method": request.method,
                                "status_code": response_status,
                                "duration_ms": duration_ms,
                                "ip_address": client_ip,
                                "user_agent": user_agent,
                                "error": True,
                            }
                            trace_id = _langfuse_client.trace(
                                name=request.url.path,
                                user_id=user_id,
                                metadata=langfuse_metadata,
                                input=request_body,
                                output=response_body_str,
                            )
                            if trace_id:
                                logger.debug(f"Langfuse Trace 已记录（错误）: {trace_id}")
                        except Exception as e:
                            logger.warning(f"记录 Langfuse Trace 失败（错误）: {e}", exc_info=True)
                except Exception as e:
                    logger.error(f"记录错误审计日志失败: {e}", exc_info=True)
            
            wrapped_response = ResponseCapture(response, captured_body_list, log_error_audit)
            raise
        finally:
            # 返回包装后的响应，这样可以在响应发送时捕获响应体
            # 审计日志会在响应发送后通过回调函数记录
            pass
        
        return wrapped_response if 'wrapped_response' in locals() else response
    
    def _should_exclude(self, path: str) -> bool:
        """检查路径是否应该排除"""
        # 检查完全匹配的路径
        if path in self.EXCLUDED_PATHS:
            return True
        # 检查路径前缀
        if any(path.startswith(prefix) for prefix in self.EXCLUDED_PREFIXES):
            return True
        return False
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        # 检查X-Forwarded-For头（代理/负载均衡器）
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # 取第一个IP（原始客户端IP）
            return forwarded_for.split(",")[0].strip()
        
        # 检查X-Real-IP头
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # 使用客户端IP
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _get_user_info(self, request: Request) -> tuple[str | None, str | None]:
        """从请求中获取用户信息"""
        try:
            # 从Authorization头获取token
            auth_header = request.headers.get("authorization")
            if not auth_header:
                return None, None
            
            # 提取token（Bearer <token>）
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
            else:
                token = auth_header
            
            # 验证token
            payload = verify_token(token)
            if not payload:
                return None, None
            
            # 从payload中获取用户ID和租户ID
            user_id = payload.get("sub")
            tenant_id = payload.get("tenant_id")
            
            return user_id, tenant_id
        except Exception as e:
            logger.warning(f"获取用户信息失败: {e}")
            return None, None
    
    async def _read_request_body(self, request: Request) -> str | None:
        """读取请求体"""
        try:
            # 检查Content-Type
            content_type = request.headers.get("content-type", "")
            
            # 只记录JSON和表单数据
            if "application/json" in content_type:
                body = await request.body()
                if len(body) > self.MAX_BODY_SIZE:
                    return f"[Body too large: {len(body)} bytes]"
                
                # 缓存请求体，以便后续路由可以读取
                async def receive():
                    return {"type": "http.request", "body": body}
                request._receive = receive
                
                try:
                    body_dict = json.loads(body)
                    # 脱敏处理
                    masked_body = mask_sensitive_data(body_dict)
                    return json.dumps(masked_body, ensure_ascii=False)
                except json.JSONDecodeError:
                    return "[Invalid JSON]"
            elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
                # 表单数据，记录为字符串
                body = await request.body()
                if len(body) > self.MAX_BODY_SIZE:
                    return f"[Body too large: {len(body)} bytes]"
                
                # 缓存请求体
                async def receive():
                    return {"type": "http.request", "body": body}
                request._receive = receive
                
                return body.decode('utf-8', errors='ignore')[:1000]  # 限制长度
            else:
                # 其他类型，不记录或只记录大小
                return None
        except Exception as e:
            logger.warning(f"读取请求体失败: {e}")
            return None
    
    async def _process_captured_body(self, body_bytes: bytes, content_type: str) -> tuple[str | None, int]:
        """处理捕获的响应体"""
        try:
            # 只记录JSON响应
            if "application/json" not in content_type:
                # 非JSON响应，只记录大小
                return None, len(body_bytes)
            
            if not body_bytes:
                return None, 0
            
            # 解码响应体
            try:
                body_str = body_bytes.decode('utf-8', errors='ignore')
            except Exception as e:
                logger.debug(f"解码响应体失败: {e}")
                return None, len(body_bytes)
            
            response_size = len(body_bytes)
            
            if response_size > self.MAX_BODY_SIZE:
                return f"[Response too large: {response_size} bytes]", response_size
            
            try:
                body_dict = json.loads(body_str)
                # 脱敏处理
                masked_body = mask_sensitive_data(body_dict)
                return json.dumps(masked_body, ensure_ascii=False), response_size
            except (json.JSONDecodeError, TypeError) as e:
                # 如果不是JSON，返回原始内容（截断）
                logger.debug(f"响应体不是有效的JSON: {e}")
                return body_str[:1000], response_size
        except Exception as e:
            logger.warning(f"处理响应体失败: {e}", exc_info=True)
            return None, len(body_bytes) if body_bytes else 0
    
    async def _log_audit(
        self,
        user_id: str | None,
        tenant_id: str | None,
        method: str,
        path: str,
        query_params: dict | None,
        request_body: str | None,
        response_status: int,
        response_body: str | None,
        request_size: int,
        response_size: int,
        duration_ms: int,
        ip_address: str,
        user_agent: str,
    ):
        """异步记录审计日志"""
        try:
            db = SessionLocal()
            try:
                # 序列化查询参数
                query_params_str = serialize_for_storage(query_params) if query_params else None
                
                # 创建审计日志
                audit_log = AuditLog(
                    user_id=user_id,
                    tenant_id=tenant_id,
                    method=method,
                    path=path,
                    query_params=query_params_str,
                    request_body=request_body,
                    response_status=response_status,
                    response_body=response_body,
                    request_size=request_size,
                    response_size=response_size,
                    duration_ms=duration_ms,
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
                
                db.add(audit_log)
                db.commit()
                logger.info(f"审计日志已记录: {method} {path} - {response_status} (用户: {user_id}, 租户: {tenant_id})")
            except Exception as e:
                db.rollback()
                logger.error(f"记录审计日志失败: {method} {path} - {e}", exc_info=True)
            finally:
                db.close()
        except Exception as e:
            logger.error(f"创建数据库会话失败: {e}", exc_info=True)

