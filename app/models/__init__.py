"""
数据模型
"""
from app.models.tenant import Tenant
from app.models.user import User
from app.models.permission import Permission
from app.models.role import Role
from app.models.config import SystemConfig, UserConfig, ConfigHistory

__all__ = ["Tenant", "User", "Permission", "Role", "SystemConfig", "UserConfig", "ConfigHistory"]

