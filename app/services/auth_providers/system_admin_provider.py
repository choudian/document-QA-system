"""
系统管理员密码认证提供方（无租户）
"""
from fastapi import HTTPException, status
from app.repositories.user_repository import UserRepository
from app.core.security import password_hasher
from app.models.user import User
from .base import AuthProvider


class SystemAdminPasswordProvider(AuthProvider):
    name = "system_admin_password"

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def authenticate(self, *, tenant_id: str, phone: str, credential: str) -> User:
        user = self.user_repo.get_system_admin_by_phone(phone)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="账号或密码错误",
            )
        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账号已停用或冻结",
            )
        if not password_hasher.verify_password(credential, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="账号或密码错误",
            )
        return user

