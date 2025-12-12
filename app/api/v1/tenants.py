"""
租户管理API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.schemas.tenant import TenantCreate, TenantUpdate, TenantResponse
from app.repositories.tenant_repository import TenantRepository
from app.repositories.user_repository import UserRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.permission_repository import PermissionRepository
from app.services.tenant_service import TenantService
from app.core.security import password_hasher

router = APIRouter()


@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
def create_tenant(tenant: TenantCreate, db: Session = Depends(get_db)):
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
    db: Session = Depends(get_db)
):
    """
    查询租户列表
    """
    tenant_service = TenantService(
        tenant_repo=TenantRepository(db),
        user_repo=UserRepository(db),
        password_hasher=password_hasher,
    )
    return tenant_service.list_tenants(skip=skip, limit=limit, status_filter=status)


@router.get("/{tenant_id}", response_model=TenantResponse)
def get_tenant(tenant_id: str, db: Session = Depends(get_db)):
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
    db: Session = Depends(get_db)
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
def delete_tenant(tenant_id: str, db: Session = Depends(get_db)):
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
    db: Session = Depends(get_db)
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

