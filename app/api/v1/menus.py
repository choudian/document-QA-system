"""
菜单管理API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.api.v1.me import get_current_user
from app.models.user import User
from app.schemas.menu import (
    MenuCreate,
    MenuUpdate,
    MenuResponse,
    MenuTreeItem,
    MenuSortRequest,
)
from app.repositories.menu_repository import MenuRepository
from app.repositories.permission_repository import PermissionRepository
from app.services.menu_service import MenuService
from app.core.permissions import require_permission

router = APIRouter()


def _convert_menu_to_tree_item(menu, all_menus) -> MenuTreeItem:
    """将菜单转换为树形结构"""
    children = []
    for child in all_menus:
        if child.parent_id == menu.id:
            children.append(_convert_menu_to_tree_item(child, all_menus))
    
    menu_dict = {
        "id": menu.id,
        "parent_id": menu.parent_id,
        "name": menu.name,
        "path": menu.path,
        "icon": menu.icon,
        "permission_code": menu.permission_code,
        "sort_order": menu.sort_order,
        "visible": menu.visible,
        "tenant_id": menu.tenant_id,
        "status": menu.status,
        "created_at": menu.created_at,
        "updated_at": menu.updated_at,
        "created_by": menu.created_by,
    }
    
    if children:
        menu_dict["children"] = children
    
    return MenuTreeItem(**menu_dict)


@router.get("/my", response_model=List[MenuTreeItem])
def get_my_menus(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取当前用户的可见菜单（动态菜单接口）
    根据用户权限过滤，返回树形结构
    """
    menu_service = MenuService(
        menu_repo=MenuRepository(db),
        permission_repo=PermissionRepository(db),
    )
    
    menus = menu_service.get_user_menus(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
    )
    
    # 转换为树形结构
    # 先找出所有根菜单
    root_menus = [m for m in menus if m.parent_id is None]
    all_menus_dict = {m.id: m for m in menus}
    
    tree_items = []
    for root_menu in root_menus:
        tree_items.append(_convert_menu_to_tree_item(root_menu, menus))
    
    return tree_items


@router.get("", response_model=List[MenuTreeItem])
def list_menus(
    tenant_id: Optional[str] = None,
    include_invisible: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _ = Depends(require_permission("system:menu:read"))
):
    """
    获取菜单列表（树形结构）
    租户管理员自动使用其tenant_id查询
    """
    # 租户管理员自动使用其tenant_id
    if not current_user.is_system_admin and current_user.tenant_id:
        if tenant_id is None:
            tenant_id = current_user.tenant_id
        elif tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权查看其他租户的菜单"
            )
    
    menu_service = MenuService(
        menu_repo=MenuRepository(db),
        permission_repo=PermissionRepository(db),
    )
    
    menus = menu_service.list_menus(
        tenant_id=tenant_id,
        include_invisible=include_invisible,
    )
    
    # 转换为树形结构
    root_menus = [m for m in menus if m.parent_id is None]
    tree_items = []
    for root_menu in root_menus:
        tree_items.append(_convert_menu_to_tree_item(root_menu, menus))
    
    return tree_items


@router.post("", response_model=MenuResponse, status_code=status.HTTP_201_CREATED)
def create_menu(
    menu: MenuCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _ = Depends(require_permission("system:menu:create"))
):
    """
    创建菜单
    租户管理员自动使用其tenant_id
    """
    # 租户管理员自动使用其tenant_id
    if not current_user.is_system_admin and current_user.tenant_id:
        if menu.tenant_id is None:
            menu.tenant_id = current_user.tenant_id
        elif menu.tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权为其他租户创建菜单"
            )
    
    menu_service = MenuService(
        menu_repo=MenuRepository(db),
        permission_repo=PermissionRepository(db),
    )
    
    return menu_service.create_menu(menu, created_by=current_user.id)


@router.get("/{menu_id}", response_model=MenuResponse)
def get_menu(
    menu_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _ = Depends(require_permission("system:menu:read"))
):
    """
    获取单个菜单
    租户管理员只能查看本租户的菜单
    """
    menu_service = MenuService(
        menu_repo=MenuRepository(db),
        permission_repo=PermissionRepository(db),
    )
    
    menu = menu_service.get_menu(menu_id)
    
    # 租户管理员只能查看本租户的菜单
    if not current_user.is_system_admin and current_user.tenant_id:
        if menu.tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权查看其他租户的菜单"
            )
    
    return menu


@router.put("/{menu_id}", response_model=MenuResponse)
def update_menu(
    menu_id: str,
    menu_update: MenuUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _ = Depends(require_permission("system:menu:update"))
):
    """
    更新菜单
    租户管理员只能更新本租户的菜单
    """
    menu_service = MenuService(
        menu_repo=MenuRepository(db),
        permission_repo=PermissionRepository(db),
    )
    
    menu = menu_service.get_menu(menu_id)
    
    # 租户管理员只能更新本租户的菜单
    if not current_user.is_system_admin and current_user.tenant_id:
        if menu.tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权更新其他租户的菜单"
            )
    
    return menu_service.update_menu(menu_id, menu_update)


@router.delete("/{menu_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_menu(
    menu_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _ = Depends(require_permission("system:menu:delete"))
):
    """
    删除菜单
    租户管理员只能删除本租户的菜单
    """
    menu_service = MenuService(
        menu_repo=MenuRepository(db),
        permission_repo=PermissionRepository(db),
    )
    
    menu = menu_service.get_menu(menu_id)
    
    # 租户管理员只能删除本租户的菜单
    if not current_user.is_system_admin and current_user.tenant_id:
        if menu.tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权删除其他租户的菜单"
            )
    
    menu_service.delete_menu(menu_id)
    return None


@router.patch("/{menu_id}/status", response_model=MenuResponse)
def update_menu_status(
    menu_id: str,
    status: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _ = Depends(require_permission("system:menu:update"))
):
    """
    启用/停用菜单
    租户管理员只能更新本租户的菜单状态
    """
    menu_service = MenuService(
        menu_repo=MenuRepository(db),
        permission_repo=PermissionRepository(db),
    )
    
    menu = menu_service.get_menu(menu_id)
    
    # 租户管理员只能更新本租户的菜单状态
    if not current_user.is_system_admin and current_user.tenant_id:
        if menu.tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权更新其他租户的菜单状态"
            )
    
    return menu_service.update_status(menu_id, status)


@router.post("/sort", status_code=status.HTTP_200_OK)
def update_menu_sort(
    payload: MenuSortRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _ = Depends(require_permission("system:menu:update"))
):
    """
    批量更新菜单排序
    """
    menu_service = MenuService(
        menu_repo=MenuRepository(db),
        permission_repo=PermissionRepository(db),
    )
    
    menu_service.update_sort_order(payload.menu_orders)
    return {"message": "菜单排序更新成功"}

