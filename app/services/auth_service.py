"""
认证领域服务
"""
from fastapi import HTTPException, status
from app.repositories.user_repository import UserRepository
from app.repositories.tenant_repository import TenantRepository
from app.core.security import create_access_token
from app.services.auth_providers.password_provider import PasswordAuthProvider
from app.services.auth_providers.sso_provider import SSOAuthProvider
from app.services.auth_providers.system_admin_provider import SystemAdminPasswordProvider
from app.services.auth_providers.base import AuthProvider
from app.models.user import User


class AuthService:
    """
    认证服务，支持多种认证提供方（策略模式），默认使用 password
    """

    def __init__(self, user_repo: UserRepository, tenant_repo: TenantRepository):
        self.user_repo = user_repo
        self.tenant_repo = tenant_repo
        # 注册可用的认证提供方
        self.providers: dict[str, AuthProvider] = {
            PasswordAuthProvider.name: PasswordAuthProvider(user_repo, tenant_repo),
            SSOAuthProvider.name: SSOAuthProvider(),
            SystemAdminPasswordProvider.name: SystemAdminPasswordProvider(user_repo),
        }

    def login(self, phone: str, credential: str, auth_type: str = "password") -> str:
        provider = self.providers.get(auth_type)
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的认证方式: {auth_type}",
            )

        # 通过手机号查询用户（手机号全局唯一）
        user = self.user_repo.get_by_phone(phone)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="手机号或密码错误",
            )
        
        # 验证密码
        from app.core.security import password_hasher
        if not password_hasher.verify_password(credential, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="手机号或密码错误",
            )
        
        # 检查用户状态
        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户已停用或冻结",
            )
        
        # 如果是系统管理员（tenant_id 为空），检查租户状态（不需要）
        # 如果是普通用户，检查租户状态
        if user.tenant_id:
            tenant = self.tenant_repo.get(user.tenant_id)
            if not tenant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="用户所属租户不存在",
                )
            if not tenant.status:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="用户所属租户已停用",
                )
        
        # 加载用户角色关系以确保数据最新
        from sqlalchemy.orm import selectinload
        user_with_roles = self.user_repo.db.query(User).options(
            selectinload(User.roles)
        ).filter(User.id == user.id).first()
        
        if user_with_roles:
            user_with_roles.update_tenant_admin_status()
            self.user_repo.db.commit()
            is_tenant_admin = user_with_roles.is_tenant_admin
            is_system_admin = user_with_roles.is_system_administrator()
        else:
            is_tenant_admin = user.is_tenant_admin if hasattr(user, 'is_tenant_admin') else False
            is_system_admin = False
        
        # 生成 token
        token = create_access_token({
            "sub": user.id,
            "tenant_id": user.tenant_id,
            "is_system_admin": is_system_admin,
            "is_tenant_admin": is_tenant_admin,
        })
        return token

