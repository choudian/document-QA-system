"""
权限Schema
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import re


class PermissionBase(BaseModel):
    """权限基础Schema"""
    code: str = Field(..., min_length=1, max_length=100, description="权限码（module:resource:action格式）")
    name: str = Field(..., min_length=1, max_length=100, description="权限名称")
    description: Optional[str] = Field(None, max_length=500, description="权限描述")
    type: str = Field(..., description="权限类型：menu-菜单，api-接口，button-按钮，tab-Tab页")
    module: str = Field(..., min_length=1, max_length=50, description="所属模块")
    tenant_id: Optional[str] = Field(None, description="租户ID（为空表示系统级权限）")
    status: bool = Field(True, description="状态：True-启用，False-停用")

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str):
        """验证权限码格式：module:resource:action"""
        pattern = re.compile(r'^[a-z][a-z0-9_]*:[a-z][a-z0-9_]*:[a-z][a-z0-9_]*$')
        if not pattern.match(v):
            raise ValueError("权限码格式不正确，应为 module:resource:action 格式（如：doc:file:read）")
        return v

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str):
        """验证权限类型"""
        allowed_types = ["menu", "api", "button", "tab"]
        if v not in allowed_types:
            raise ValueError(f"权限类型必须是以下之一：{', '.join(allowed_types)}")
        return v


class PermissionCreate(PermissionBase):
    """创建权限Schema"""
    pass


class PermissionUpdate(BaseModel):
    """更新权限Schema"""
    code: Optional[str] = Field(None, min_length=1, max_length=100, description="权限码（module:resource:action格式）")
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="权限名称")
    description: Optional[str] = Field(None, max_length=500, description="权限描述")
    type: Optional[str] = Field(None, description="权限类型：menu-菜单，api-接口，button-按钮，tab-Tab页")
    module: Optional[str] = Field(None, min_length=1, max_length=50, description="所属模块")
    status: Optional[bool] = Field(None, description="状态：True-启用，False-停用")

    @field_validator("code")
    @classmethod
    def validate_code(cls, v):
        """验证权限码格式：module:resource:action"""
        if v is None:
            return v
        pattern = re.compile(r'^[a-z][a-z0-9_]*:[a-z][a-z0-9_]*:[a-z][a-z0-9_]*$')
        if not pattern.match(v):
            raise ValueError("权限码格式不正确，应为 module:resource:action 格式（如：doc:file:read）")
        return v

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        """验证权限类型"""
        if v is None:
            return v
        allowed_types = ["menu", "api", "button", "tab"]
        if v not in allowed_types:
            raise ValueError(f"权限类型必须是以下之一：{', '.join(allowed_types)}")
        return v


class PermissionResponse(PermissionBase):
    """权限响应Schema"""
    id: str
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    
    class Config:
        from_attributes = True

