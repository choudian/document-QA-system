"""
用户管理API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.api.v1.me import get_current_user
from app.models.user import User
from app.models.tenant import Tenant
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.core.security import password_hasher
from app.core.permissions import require_permission

router = APIRouter()


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    _ = Depends(require_permission("system:user:create"))
):
    """
    创建用户
    租户管理员自动使用其tenant_id
    """
    # 如果是租户管理员，自动使用其tenant_id
    if not current_user.is_system_admin and current_user.tenant_id:
        if user.tenant_id is None:
            user.tenant_id = current_user.tenant_id
        elif user.tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权为其他租户创建用户"
            )
    elif current_user.is_system_admin:
        # 系统管理员必须指定tenant_id
        if user.tenant_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="系统管理员必须指定tenant_id"
            )
    
    # 检查租户是否存在
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"租户 ID '{user.tenant_id}' 不存在"
        )
    
    # 检查租户是否启用
    if not tenant.status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"租户 '{tenant.name}' 已停用，无法创建用户"
        )
    
    # 检查用户名在租户内是否已存在
    existing_user = db.query(User).filter(
        User.tenant_id == user.tenant_id,
        User.username == user.username
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"租户内用户名 '{user.username}' 已存在"
        )
    
    # 检查手机号全局唯一性（手机号必须全局唯一）
    existing_phone = db.query(User).filter(
        User.phone == user.phone
    ).first()
    if existing_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"手机号 '{user.phone}' 已被占用"
        )

    db_user = User(
        tenant_id=user.tenant_id,
        username=user.username,
        phone=user.phone,
        password_hash=password_hasher.hash_password(user.password),
        status="active",  # 默认启用
        is_tenant_admin=False,  # 创建时默认为False，后续通过角色分配自动更新
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.get("", response_model=List[UserResponse])
def list_users(
    tenant_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    _ = Depends(require_permission("system:user:read"))
):
    """
    查询用户列表
    租户管理员自动使用其tenant_id
    """
    # 如果是租户管理员，自动使用其tenant_id
    if not current_user.is_system_admin and current_user.tenant_id:
        if tenant_id is None:
            tenant_id = current_user.tenant_id
        elif tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权查看其他租户的用户"
            )
    elif current_user.is_system_admin:
        # 系统管理员必须指定tenant_id
        if tenant_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="系统管理员必须指定tenant_id"
            )
    
    query = db.query(User)
    
    # 租户隔离：必须指定 tenant_id
    if tenant_id:
        query = query.filter(User.tenant_id == tenant_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="必须指定 tenant_id 参数"
        )
    
    if status:
        query = query.filter(User.status == status)
    
    users = query.offset(skip).limit(limit).all()
    return users


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    _ = Depends(require_permission("system:user:read"))
):
    """
    查询单个用户
    租户管理员只能查看本租户的用户
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户 ID '{user_id}' 不存在"
        )
    
    # 租户管理员只能查看本租户的用户
    if not current_user.is_system_admin and current_user.tenant_id:
        if user.tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权查看其他租户的用户"
            )
    
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    _ = Depends(require_permission("system:user:update"))
):
    """
    更新用户
    租户管理员只能更新本租户的用户
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户 ID '{user_id}' 不存在"
        )
    
    # 租户管理员只能更新本租户的用户
    if not current_user.is_system_admin and current_user.tenant_id:
        if user.tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权更新其他租户的用户"
            )
        # 租户管理员不能修改用户的tenant_id
        if user_update.tenant_id is not None and user_update.tenant_id != user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权修改用户的租户"
            )
    
    # 如果更新用户名，检查在租户内是否重复
    if user_update.username and user_update.username != user.username:
        existing_user = db.query(User).filter(
            User.tenant_id == user.tenant_id,
            User.username == user_update.username
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"租户内用户名 '{user_update.username}' 已存在"
            )
        user.username = user_update.username
    
    # 更新其他字段
    if user_update.phone is not None:
        if user_update.phone != user.phone:
            # 检查手机号全局唯一性（手机号必须全局唯一）
            existing_phone = db.query(User).filter(
                User.phone == user_update.phone
            ).first()
            if existing_phone:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"手机号 '{user_update.phone}' 已被占用"
                )
        user.phone = user_update.phone
    if user_update.password is not None:
        user.password_hash = password_hasher.hash_password(user_update.password)
    if user_update.status is not None:
        user.status = user_update.status
    # is_tenant_admin 字段通过角色自动管理，不再手动设置
    # 如果角色发生变化，需要重新加载角色关系后调用 user.update_tenant_admin_status()
    if user_update.tenant_id is not None and current_user.is_system_admin:
        # 只有系统管理员可以修改用户的tenant_id
        user.tenant_id = user_update.tenant_id
    
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    _ = Depends(require_permission("system:user:delete"))
):
    """
    删除用户
    租户管理员只能删除本租户的用户
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户 ID '{user_id}' 不存在"
        )
    
    # 租户管理员只能删除本租户的用户
    if not current_user.is_system_admin and current_user.tenant_id:
        if user.tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权删除其他租户的用户"
            )
    
    db.delete(user)
    db.commit()
    return None


@router.patch("/{user_id}/status", response_model=UserResponse)
def update_user_status(
    user_id: str,
    status: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    _ = Depends(require_permission("system:user:update"))
):
    """
    启用/冻结用户
    租户管理员只能更新本租户的用户状态
    """
    if status not in ["active", "frozen"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="状态必须是 'active' 或 'frozen'"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户 ID '{user_id}' 不存在"
        )
    
    # 租户管理员只能更新本租户的用户状态
    if not current_user.is_system_admin and current_user.tenant_id:
        if user.tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权更新其他租户的用户状态"
            )
    
    user.status = status
    db.commit()
    db.refresh(user)
    return user

