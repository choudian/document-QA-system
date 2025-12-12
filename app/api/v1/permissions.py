"""
权限管理API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.api.v1.me import get_current_user
from app.schemas.permission import PermissionCreate, PermissionUpdate, PermissionResponse
from app.repositories.permission_repository import PermissionRepository
from app.services.permission_service import PermissionService

router = APIRouter()


@router.post("", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
def create_permission(permission: PermissionCreate, db: Session = Depends(get_db)):
    """
    创建权限
    """
    permission_service = PermissionService(
        permission_repo=PermissionRepository(db),
    )
    return permission_service.create_permission(permission)


@router.get("", response_model=List[PermissionResponse])
def list_permissions(
    skip: int = 0,
    limit: int = 100,
    module: Optional[str] = None,
    type: Optional[str] = None,
    status: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    查询权限列表
    支持按模块、类型、状态过滤
    租户管理员自动使用其tenant_id查询，本租户的权限（不包括租户管理相关权限）
    """
    # 租户ID直接从当前登录用户中获取
    tenant_id = None
    if not current_user.is_system_admin:
        # 非系统管理员必须关联租户
        if not current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户未关联租户，无法查询权限"
            )
        tenant_id = current_user.tenant_id
    
    permission_service = PermissionService(
        permission_repo=PermissionRepository(db),
    )
    permissions = permission_service.list_permissions(
        skip=skip,
        limit=limit,
        tenant_id=tenant_id,
        module=module,
        type=type,
        status_filter=status,
    )
    
    # 非系统管理员需要过滤掉租户管理相关的权限（system:tenant:*）
    if not current_user.is_system_admin:
        permissions = [p for p in permissions if not p.code.startswith("system:tenant:")]
    
    return permissions


@router.get("/{permission_id}", response_model=PermissionResponse)
def get_permission(permission_id: str, db: Session = Depends(get_db)):
    """
    查询单个权限
    """
    permission_service = PermissionService(
        permission_repo=PermissionRepository(db),
    )
    return permission_service.get_permission(permission_id)


@router.put("/{permission_id}", response_model=PermissionResponse)
def update_permission(
    permission_id: str,
    permission_update: PermissionUpdate,
    db: Session = Depends(get_db)
):
    """
    更新权限
    """
    permission_service = PermissionService(
        permission_repo=PermissionRepository(db),
    )
    return permission_service.update_permission(permission_id, permission_update)


@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_permission(permission_id: str, db: Session = Depends(get_db)):
    """
    删除权限
    """
    permission_service = PermissionService(
        permission_repo=PermissionRepository(db),
    )
    permission_service.delete_permission(permission_id)
    return None


@router.patch("/{permission_id}/status", response_model=PermissionResponse)
def update_permission_status(
    permission_id: str,
    status: bool,
    db: Session = Depends(get_db)
):
    """
    启用/停用权限
    """
    permission_service = PermissionService(
        permission_repo=PermissionRepository(db),
    )
    return permission_service.update_status(permission_id, status)

