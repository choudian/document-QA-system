"""
角色Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class RoleBase(BaseModel):
    """角色基础Schema"""
    name: str = Field(..., min_length=1, max_length=100, description="角色名称")
    description: Optional[str] = Field(None, max_length=500, description="角色描述")
    tenant_id: Optional[str] = Field(None, description="租户ID，None表示系统级角色（如租户管理员）")
    status: bool = Field(True, description="状态：True-启用，False-停用")


class RoleCreate(RoleBase):
    """创建角色Schema"""
    pass


class RoleUpdate(BaseModel):
    """更新角色Schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="角色名称")
    description: Optional[str] = Field(None, max_length=500, description="角色描述")
    status: Optional[bool] = Field(None, description="状态：True-启用，False-停用")


class RoleResponse(RoleBase):
    """角色响应Schema"""
    id: str
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    
    class Config:
        from_attributes = True


class RoleWithPermissions(RoleResponse):
    """带权限的角色响应Schema"""
    permission_ids: List[str] = Field(default_factory=list, description="权限ID列表")
    
    class Config:
        from_attributes = True


class AssignPermissionsRequest(BaseModel):
    """分配权限请求Schema"""
    permission_ids: List[str] = Field(..., description="权限ID列表")


class AssignRolesRequest(BaseModel):
    """分配角色请求Schema"""
    role_ids: List[str] = Field(..., description="角色ID列表")


class AssignUsersRequest(BaseModel):
    """分配用户请求Schema"""
    user_ids: List[str] = Field(..., description="用户ID列表")

