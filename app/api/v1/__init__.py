"""
API v1路由
"""
from fastapi import APIRouter
from app.api.v1 import tenants, users, auth, system_admin, permissions, roles, me, menus, configs, audit_logs

router = APIRouter()

router.include_router(tenants.router, prefix="/tenants", tags=["租户管理"])
router.include_router(users.router, prefix="/users", tags=["用户管理"])
router.include_router(auth.router, prefix="/auth", tags=["认证"])
router.include_router(system_admin.router, prefix="/system-admin", tags=["系统管理员"])
router.include_router(permissions.router, prefix="/permissions", tags=["权限管理"])
router.include_router(roles.router, prefix="/roles", tags=["角色管理"])
router.include_router(menus.router, prefix="/menus", tags=["菜单管理"])
router.include_router(configs.router, prefix="/configs", tags=["配置管理"])
router.include_router(audit_logs.router, prefix="/audit-logs", tags=["审计日志"])
router.include_router(me.router, prefix="/me", tags=["当前用户"])

