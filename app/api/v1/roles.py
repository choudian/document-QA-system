"""
角色管理API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.api.v1.me import get_current_user
from app.schemas.role import (
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    AssignPermissionsRequest,
    AssignRolesRequest,
    AssignUsersRequest,
)
from app.repositories.role_repository import RoleRepository
from app.repositories.permission_repository import PermissionRepository
from app.repositories.user_repository import UserRepository
from app.services.role_service import RoleService

router = APIRouter()


@router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(
    role: RoleCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    创建角色
    非系统管理员自动使用其tenant_id，不能创建系统级角色
    """
    # 非系统管理员必须使用其tenant_id，不能创建系统级角色
    if not current_user.is_system_admin:
        if not current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户未关联租户，无法创建角色"
            )
        # 强制使用当前用户的tenant_id
        role.tenant_id = current_user.tenant_id
    # 系统管理员可以创建系统级角色（tenant_id为None）或租户级角色
    
    role_service = RoleService(
        role_repo=RoleRepository(db),
        permission_repo=PermissionRepository(db),
        user_repo=UserRepository(db),
    )
    return role_service.create_role(role)


@router.get("", response_model=List[RoleResponse])
def list_roles(
    skip: int = 0,
    limit: int = 100,
    status: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    查询角色列表
    支持按状态过滤
    租户管理员自动使用其tenant_id查询，本租户的角色
    """
    # 租户ID直接从当前登录用户中获取
    # 系统管理员：tenant_id=None 表示只查询系统级角色（tenant_id IS NULL）
    # 非系统管理员：tenant_id=xxx 表示只查询该租户的角色（tenant_id = xxx）
    tenant_id = None
    if not current_user.is_system_admin:
        # 非系统管理员必须关联租户
        if not current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户未关联租户，无法查询角色"
            )
        tenant_id = current_user.tenant_id
    # 系统管理员：tenant_id=None，Repository会只查询系统级角色（tenant_id IS NULL）
    
    role_service = RoleService(
        role_repo=RoleRepository(db),
        permission_repo=PermissionRepository(db),
        user_repo=UserRepository(db),
    )
    return role_service.list_roles(
        skip=skip,
        limit=limit,
        tenant_id=tenant_id,
        status_filter=status,
    )


@router.get("/{role_id}", response_model=RoleResponse)
def get_role(role_id: str, db: Session = Depends(get_db)):
    """
    查询单个角色
    """
    role_service = RoleService(
        role_repo=RoleRepository(db),
        permission_repo=PermissionRepository(db),
        user_repo=UserRepository(db),
    )
    return role_service.get_role(role_id)


@router.put("/{role_id}", response_model=RoleResponse)
def update_role(
    role_id: str,
    role_update: RoleUpdate,
    db: Session = Depends(get_db)
):
    """
    更新角色
    """
    role_service = RoleService(
        role_repo=RoleRepository(db),
        permission_repo=PermissionRepository(db),
        user_repo=UserRepository(db),
    )
    return role_service.update_role(role_id, role_update)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(role_id: str, db: Session = Depends(get_db)):
    """
    删除角色
    """
    role_service = RoleService(
        role_repo=RoleRepository(db),
        permission_repo=PermissionRepository(db),
        user_repo=UserRepository(db),
    )
    role_service.delete_role(role_id)
    return None


@router.patch("/{role_id}/status", response_model=RoleResponse)
def update_role_status(
    role_id: str,
    status: bool,
    db: Session = Depends(get_db)
):
    """
    启用/停用角色
    """
    role_service = RoleService(
        role_repo=RoleRepository(db),
        permission_repo=PermissionRepository(db),
        user_repo=UserRepository(db),
    )
    return role_service.update_status(role_id, status)


@router.post("/{role_id}/permissions", response_model=RoleResponse)
def assign_permissions(
    role_id: str,
    payload: AssignPermissionsRequest,
    db: Session = Depends(get_db)
):
    """
    为角色分配权限
    """
    role_service = RoleService(
        role_repo=RoleRepository(db),
        permission_repo=PermissionRepository(db),
        user_repo=UserRepository(db),
    )
    return role_service.assign_permissions(role_id, payload)


@router.get("/{role_id}/permissions", response_model=List[dict])
def get_role_permissions(role_id: str, db: Session = Depends(get_db)):
    """
    获取角色的权限列表
    """
    from app.schemas.permission import PermissionResponse
    
    role_service = RoleService(
        role_repo=RoleRepository(db),
        permission_repo=PermissionRepository(db),
        user_repo=UserRepository(db),
    )
    permissions = role_service.get_role_permissions(role_id)
    return [PermissionResponse.model_validate(p).model_dump() for p in permissions]


@router.post("/users/{user_id}/roles", response_model=dict)
def assign_roles_to_user(
    user_id: str,
    payload: AssignRolesRequest,
    db: Session = Depends(get_db)
):
    """
    为用户分配角色
    """
    from app.schemas.user import UserResponse
    
    role_service = RoleService(
        role_repo=RoleRepository(db),
        permission_repo=PermissionRepository(db),
        user_repo=UserRepository(db),
    )
    user = role_service.assign_roles_to_user(user_id, payload)
    return UserResponse.model_validate(user).model_dump()


@router.post("/{role_id}/users", response_model=RoleResponse)
def assign_users_to_role(
    role_id: str,
    payload: AssignUsersRequest,
    db: Session = Depends(get_db)
):
    """
    为角色分配用户
    """
    role_service = RoleService(
        role_repo=RoleRepository(db),
        permission_repo=PermissionRepository(db),
        user_repo=UserRepository(db),
    )
    return role_service.assign_users_to_role(role_id, payload)


@router.get("/{role_id}/users", response_model=List[dict])
def get_role_users(role_id: str, db: Session = Depends(get_db)):
    """
    获取角色的用户列表
    """
    from app.schemas.user import UserResponse
    
    role_service = RoleService(
        role_repo=RoleRepository(db),
        permission_repo=PermissionRepository(db),
        user_repo=UserRepository(db),
    )
    users = role_service.get_role_users(role_id)
    return [UserResponse.model_validate(u).model_dump() for u in users]

