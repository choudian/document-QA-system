"""
SSO / OIDC 等认证提供方占位，便于后续扩展
"""
from fastapi import HTTPException, status
from app.models.user import User
from .base import AuthProvider


class SSOAuthProvider(AuthProvider):
    name = "sso"

    def authenticate(self, *, tenant_id: str, phone: str, credential: str) -> User:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="SSO/OIDC 认证尚未实现（占位）",
        )

