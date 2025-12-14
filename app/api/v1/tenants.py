"""
租户管理API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.api.v1.me import get_current_user
from app.schemas.tenant import TenantCreate, TenantUpdate, TenantResponse
from app.repositories.tenant_repository import TenantRepository
from app.repositories.user_repository import UserRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.permission_repository import PermissionRepository
from app.services.tenant_service import TenantService
from app.core.security import password_hasher
from app.core.permissions import require_permission

router = APIRouter()


@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
def create_tenant(
    tenant: TenantCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    _ = Depends(require_permission("system:tenant:create"))
):
    """
    创建租户
    """
    tenant_service = TenantService(
        tenant_repo=TenantRepository(db),
        user_repo=UserRepository(db),
        password_hasher=password_hasher,
        role_repo=RoleRepository(db),
        permission_repo=PermissionRepository(db),
    )
    return tenant_service.create_tenant(tenant)


@router.get("", response_model=List[TenantResponse])
def list_tenants(
    skip: int = 0,
    limit: int = 100,
    status: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    _ = Depends(require_permission("system:tenant:read"))
):
    """
    查询租户列表
    系统管理员可以查看所有租户，租户管理员只能查看自己的租户
    """
    tenant_service = TenantService(
        tenant_repo=TenantRepository(db),
        user_repo=UserRepository(db),
        password_hasher=password_hasher,
    )
    
    # 系统管理员可以查看所有租户
    if current_user.is_system_admin:
        return tenant_service.list_tenants(skip=skip, limit=limit, status_filter=status)
    
    # 租户管理员只能查看自己的租户
    if current_user.is_tenant_admin and current_user.tenant_id:
        tenant = tenant_service.get_tenant(current_user.tenant_id)
        return [tenant]
    
    # 普通用户不应该有 system:tenant:read 权限，但如果通过了权限检查，返回空列表
    return []


@router.get("/{tenant_id}", response_model=TenantResponse)
def get_tenant(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    _ = Depends(require_permission("system:tenant:read"))
):
    """
    查询单个租户
    """
    tenant_service = TenantService(
        tenant_repo=TenantRepository(db),
        user_repo=UserRepository(db),
        password_hasher=password_hasher,
    )
    return tenant_service.get_tenant(tenant_id)


@router.put("/{tenant_id}", response_model=TenantResponse)
def update_tenant(
    tenant_id: str,
    tenant_update: TenantUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    _ = Depends(require_permission("system:tenant:update"))
):
    """
    更新租户
    """
    tenant_service = TenantService(
        tenant_repo=TenantRepository(db),
        user_repo=UserRepository(db),
        password_hasher=password_hasher,
    )
    return tenant_service.update_tenant(tenant_id, tenant_update)


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tenant(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    _ = Depends(require_permission("system:tenant:delete"))
):
    """
    删除租户
    """
    tenant_service = TenantService(
        tenant_repo=TenantRepository(db),
        user_repo=UserRepository(db),
        password_hasher=password_hasher,
    )
    tenant_service.delete_tenant(tenant_id)
    return None


@router.patch("/{tenant_id}/status", response_model=TenantResponse)
def update_tenant_status(
    tenant_id: str,
    status: bool,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    _ = Depends(require_permission("system:tenant:update"))
):
    """
    启用/停用租户
    """
    tenant_service = TenantService(
        tenant_repo=TenantRepository(db),
        user_repo=UserRepository(db),
        password_hasher=password_hasher,
    )
    return tenant_service.update_status(tenant_id, status)

