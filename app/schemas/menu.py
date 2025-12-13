"""
菜单Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class MenuBase(BaseModel):
    """菜单基础Schema"""
    name: str = Field(..., min_length=1, max_length=100, description="菜单名称")
    path: Optional[str] = Field(None, max_length=200, description="路由路径")
    icon: Optional[str] = Field(None, max_length=50, description="图标名称（Ant Design图标名称）")
    permission_code: Optional[str] = Field(None, max_length=100, description="关联的权限码（type='menu'的权限）")
    sort_order: int = Field(0, description="排序序号")
    visible: bool = Field(True, description="是否可见")
    parent_id: Optional[str] = Field(None, description="父菜单ID")


class MenuCreate(MenuBase):
    """创建菜单Schema"""
    tenant_id: Optional[str] = Field(None, description="租户ID（None表示系统级菜单）")


class MenuUpdate(BaseModel):
    """更新菜单Schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="菜单名称")
    path: Optional[str] = Field(None, max_length=200, description="路由路径")
    icon: Optional[str] = Field(None, max_length=50, description="图标名称")
    permission_code: Optional[str] = Field(None, max_length=100, description="关联的权限码")
    sort_order: Optional[int] = Field(None, description="排序序号")
    visible: Optional[bool] = Field(None, description="是否可见")
    parent_id: Optional[str] = Field(None, description="父菜单ID")
    status: Optional[bool] = Field(None, description="状态：True-启用，False-停用")


class MenuResponse(MenuBase):
    """菜单响应Schema"""
    id: str
    tenant_id: Optional[str]
    status: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    
    class Config:
        from_attributes = True


class MenuTreeItem(MenuResponse):
    """菜单树节点Schema"""
    children: Optional[List['MenuTreeItem']] = None


class MenuTreeResponse(BaseModel):
    """菜单树响应Schema"""
    items: List[MenuTreeItem]


class MenuSortRequest(BaseModel):
    """菜单排序请求Schema"""
    menu_orders: List[dict] = Field(..., description="菜单排序列表，格式：[{'id': 'menu_id', 'sort_order': 0}]")


# 更新前向引用
MenuTreeItem.model_rebuild()

