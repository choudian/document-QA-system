"""
系统管理员初始化与管理（简化：仅首个创建，无租户关系）
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.system_admin import SystemAdminInitRequest
from app.repositories.user_repository import UserRepository
from app.repositories.role_repository import RoleRepository
from app.core.security import password_hasher
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/exists")
def system_admin_exists(db: Session = Depends(get_db)):
    """
    查询是否已存在系统管理员
    """
    user_repo = UserRepository(db)
    return {"exists": user_repo.has_system_admin()}


@router.post("/init", status_code=status.HTTP_201_CREATED)
def init_system_admin(payload: SystemAdminInitRequest, db: Session = Depends(get_db)):
    """
    初始化系统管理员：
    - 若已存在系统管理员则拒绝再次创建
    - 与租户无关，tenant_id 为空，is_system_admin=True
    """
    user_repo = UserRepository(db)

    if user_repo.has_system_admin():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="系统管理员已存在",
        )

    # 检查手机号全局唯一
    existing_phone_user = user_repo.get_system_admin_by_phone(payload.phone)
    if existing_phone_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="手机号已被占用",
        )

    db_user = User(
        tenant_id=None,
        username=payload.username,
        phone=payload.phone,
        password_hash=password_hasher.hash_password(payload.password),
        status="active",
        is_tenant_admin=False,
        is_system_admin=True,
    )
    user_repo.add(db_user)
    user_repo.flush()  # 获取用户ID
    
    # 为系统管理员分配"系统管理员"角色
    role_repo = RoleRepository(db)
    system_admin_role = role_repo.get_by_name_in_tenant(None, "系统管理员")
    if system_admin_role:
        db_user.roles = [system_admin_role]
        # 自动更新 is_tenant_admin 状态
        db_user.update_tenant_admin_status()
        logger.info(f"为系统管理员用户 '{payload.username}' 分配了系统管理员角色")
    else:
        logger.warning("系统管理员角色不存在，请先运行初始化。用户已创建但未分配角色")
    
    user_repo.commit()
    return {"message": "系统管理员创建成功"}

