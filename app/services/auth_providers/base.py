"""
认证提供方抽象，便于后续扩展（密码、SSO、MFA 等）
"""
from abc import ABC, abstractmethod
from app.models.user import User


class AuthProvider(ABC):
    name: str

    @abstractmethod
    def authenticate(self, *, tenant_id: str, phone: str, credential: str) -> User:
        """
        认证用户，成功返回 User，失败抛出 HTTPException
        """
        raise NotImplementedError

