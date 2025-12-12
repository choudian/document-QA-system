"""
当前用户信息API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_token
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserResponse

router = APIRouter()
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """获取当前登录用户，优先从token中获取信息，减少数据库查询"""
    token = credentials.credentials
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的token",
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token中缺少用户ID",
        )
    
    # 从token中获取用户信息（tenant_id, is_tenant_admin）
    token_tenant_id = payload.get("tenant_id")
    token_is_tenant_admin = payload.get("is_tenant_admin", False)
    
    # 查询数据库获取完整的用户信息，并加载角色关系
    from sqlalchemy.orm import selectinload
    from app.models.user import User
    from app.models.role import Role
    
    user_repo = UserRepository(db)
    # 加载用户及其角色关系
    db_user = db.query(User).options(
        selectinload(User.roles)
    ).filter(User.id == user_id).first()
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
        )
    
    # 通过角色判断是否是系统管理员
    db_user.is_system_admin = db_user.is_system_administrator()
    # 更新租户管理员状态
    db_user.update_tenant_admin_status()
    
    # 使用token中的tenant_id（登录时的状态）
    if token_tenant_id is not None:
        db_user.tenant_id = token_tenant_id
    
    return db_user


@router.get("", response_model=UserResponse)
def get_me(current_user = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user


@router.get("/permissions", response_model=list)
def get_my_permissions(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的权限列表"""
    from sqlalchemy.orm import selectinload
    from app.models.user import User
    from app.models.role import Role
    
    # 所有用户（包括系统管理员）都通过角色获取权限
    # 使用selectinload预加载角色和权限
    user_with_roles = db.query(User).options(
        selectinload(User.roles).selectinload(Role.permissions)
    ).filter(User.id == current_user.id).first()
    
    if not user_with_roles:
        return []
    
    permissions = []
    if user_with_roles.roles:
        for role in user_with_roles.roles:
            if role.status:  # 只获取启用角色的权限
                if role.permissions:
                    for permission in role.permissions:
                        if permission.status:  # 只获取启用状态的权限
                            permissions.append({
                                "code": permission.code,
                                "name": permission.name,
                                "type": permission.type,
                            })
    
    # 去重
    seen = set()
    unique_permissions = []
    for perm in permissions:
        if perm["code"] not in seen:
            seen.add(perm["code"])
            unique_permissions.append(perm)
    
    return unique_permissions

