"""
租户Schema
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TenantBase(BaseModel):
    """租户基础Schema"""
    code: str = Field(..., min_length=1, max_length=50, description="租户编码")
    name: str = Field(..., min_length=1, max_length=100, description="租户名称")
    description: Optional[str] = Field(None, max_length=500, description="描述")


class TenantCreate(TenantBase):
    """创建租户Schema"""


class TenantUpdate(BaseModel):
    """更新租户Schema"""
    code: Optional[str] = Field(None, min_length=1, max_length=50, description="租户编码")
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="租户名称")
    description: Optional[str] = Field(None, max_length=500, description="描述")
    status: Optional[bool] = Field(None, description="状态：True-启用，False-停用")


class TenantResponse(TenantBase):
    """租户响应Schema"""
    id: str
    status: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    
    class Config:
        from_attributes = True

