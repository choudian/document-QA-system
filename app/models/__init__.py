"""
数据模型
"""
from app.models.tenant import Tenant
from app.models.user import User
from app.models.permission import Permission
from app.models.role import Role

__all__ = ["Tenant", "User", "Permission", "Role"]

