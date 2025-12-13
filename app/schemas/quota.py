"""
额度相关 Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class QuotaInfo(BaseModel):
    """额度信息"""
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    quota_type: str = Field(..., description="额度类型：api_calls/storage/bandwidth")
    limit: Optional[int] = Field(None, description="限制值（None 表示无限制）")
    used: int = Field(0, description="已使用量")
    remaining: Optional[int] = Field(None, description="剩余量（None 表示无限制）")
    reset_at: Optional[str] = Field(None, description="重置时间（ISO 格式）")


class QuotaRequest(BaseModel):
    """设置额度请求"""
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    quota_type: str = Field(..., description="额度类型：api_calls/storage/bandwidth")
    limit: Optional[int] = Field(None, description="限制值（None 表示无限制）")


class RateLimitInfo(BaseModel):
    """速率限制信息"""
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    limit_type: str = Field(..., description="限制类型：requests_per_second/requests_per_minute")
    limit_value: Optional[int] = Field(None, description="限制值（None 表示无限制）")
    current_rate: float = Field(0.0, description="当前速率")


class RateLimitRequest(BaseModel):
    """设置速率限制请求"""
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    limit_type: str = Field(..., description="限制类型：requests_per_second/requests_per_minute")
    limit_value: Optional[int] = Field(None, description="限制值（None 表示无限制）")

