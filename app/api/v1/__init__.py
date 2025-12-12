"""
API v1路由
"""
from fastapi import APIRouter
from app.api.v1 import tenants, users, auth, system_admin, permissions, roles, me

router = APIRouter()

router.include_router(tenants.router, prefix="/tenants", tags=["租户管理"])
router.include_router(users.router, prefix="/users", tags=["用户管理"])
router.include_router(auth.router, prefix="/auth", tags=["认证"])
router.include_router(system_admin.router, prefix="/system-admin", tags=["系统管理员"])
router.include_router(permissions.router, prefix="/permissions", tags=["权限管理"])
router.include_router(roles.router, prefix="/roles", tags=["角色管理"])
router.include_router(me.router, prefix="/me", tags=["当前用户"])

