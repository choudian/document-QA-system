"""
基于手机号+密码的认证提供方
"""
from fastapi import HTTPException, status
from app.repositories.user_repository import UserRepository
from app.repositories.tenant_repository import TenantRepository
from app.core.security import password_hasher
from app.models.user import User
from .base import AuthProvider


class PasswordAuthProvider(AuthProvider):
    name = "password"

    def __init__(self, user_repo: UserRepository, tenant_repo: TenantRepository):
        self.user_repo = user_repo
        self.tenant_repo = tenant_repo

    def authenticate(self, *, tenant_id: str, phone: str, credential: str) -> User:
        # 租户检查
        tenant = self.tenant_repo.get(tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="租户不存在",
            )
        if not tenant.status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="租户已停用",
            )

        # 用户检查
        user = self.user_repo.get_by_phone_in_tenant(tenant_id, phone)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="手机号或密码错误",
            )
        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户已停用或冻结",
            )

        if not password_hasher.verify_password(credential, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="手机号或密码错误",
            )

        return user

