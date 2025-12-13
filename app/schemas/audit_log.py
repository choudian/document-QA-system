"""
审计日志Schema定义
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AuditLogResponse(BaseModel):
    """审计日志响应模型"""
    id: str = Field(..., description="日志ID")
    user_id: Optional[str] = Field(None, description="用户ID")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    method: str = Field(..., description="HTTP方法")
    path: str = Field(..., description="请求路径")
    query_params: Optional[str] = Field(None, description="查询参数（JSON）")
    request_body: Optional[str] = Field(None, description="请求体（JSON，已脱敏）")
    response_status: int = Field(..., description="响应状态码")
    response_body: Optional[str] = Field(None, description="响应体（JSON，已脱敏）")
    request_size: Optional[int] = Field(None, description="请求大小（字节）")
    response_size: Optional[int] = Field(None, description="响应大小（字节）")
    duration_ms: int = Field(..., description="请求耗时（毫秒）")
    ip_address: Optional[str] = Field(None, description="客户端IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """审计日志列表响应模型"""
    items: list[AuditLogResponse] = Field(..., description="日志列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")


class AuditLogQueryParams(BaseModel):
    """审计日志查询参数模型"""
    user_id: Optional[str] = Field(None, description="用户ID")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    method: Optional[str] = Field(None, description="HTTP方法")
    path: Optional[str] = Field(None, description="请求路径（模糊匹配）")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页大小")

