"""
租户领域服务
"""
from typing import Optional
from fastapi import HTTPException, status
from app.models.tenant import Tenant
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.schemas.tenant import TenantCreate, TenantUpdate
from app.repositories.tenant_repository import TenantRepository
from app.repositories.user_repository import UserRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.permission_repository import PermissionRepository
from app.core.security import PasswordHasher


class TenantService:
    def __init__(
        self,
        tenant_repo: TenantRepository,
        user_repo: UserRepository,
        password_hasher: PasswordHasher,
        role_repo: Optional[RoleRepository] = None,
        permission_repo: Optional[PermissionRepository] = None,
    ):
        self.tenant_repo = tenant_repo
        self.user_repo = user_repo
        self.password_hasher = password_hasher
        self.role_repo = role_repo
        self.permission_repo = permission_repo

    def create_tenant(self, tenant: TenantCreate) -> Tenant:
        # 唯一校验
        if self.tenant_repo.get_by_code(tenant.code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"租户编码 '{tenant.code}' 已存在",
            )
        if self.tenant_repo.get_by_name(tenant.name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"租户名称 '{tenant.name}' 已存在",
            )

        db_tenant = Tenant(
            code=tenant.code,
            name=tenant.name,
            description=tenant.description,
            status=True,
        )

        try:
            self.tenant_repo.add(db_tenant)
            self.tenant_repo.flush()  # 获取租户ID

            # 为租户创建默认的"租户管理员"角色（如果不存在）
            if self.role_repo and self.permission_repo:
                try:
                    self._create_tenant_admin_role(db_tenant.id)
                except Exception as e:
                    # 如果创建角色失败，记录日志但不阻止租户创建
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"创建租户管理员角色失败: {e}，租户已创建但角色未创建")

            self.tenant_repo.commit()
            self.tenant_repo.refresh(db_tenant)
            return db_tenant
        except HTTPException:
            self.tenant_repo.rollback()
            raise
        except Exception as e:
            self.tenant_repo.rollback()
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"创建租户失败: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"创建租户失败: {str(e)}",
            )

    def list_tenants(self, skip: int = 0, limit: int = 100, status_filter: Optional[bool] = None):
        return self.tenant_repo.list(skip=skip, limit=limit, status=status_filter)

    def get_tenant(self, tenant_id: str) -> Tenant:
        tenant = self.tenant_repo.get(tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"租户 ID '{tenant_id}' 不存在",
            )
        return tenant

    def update_tenant(self, tenant_id: str, payload: TenantUpdate) -> Tenant:
        tenant = self.get_tenant(tenant_id)

        if payload.code and payload.code != tenant.code:
            if self.tenant_repo.get_by_code(payload.code):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"租户编码 '{payload.code}' 已存在",
                )
            tenant.code = payload.code

        if payload.name and payload.name != tenant.name:
            if self.tenant_repo.get_by_name(payload.name):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"租户名称 '{payload.name}' 已存在",
                )
            tenant.name = payload.name

        if payload.description is not None:
            tenant.description = payload.description
        if payload.status is not None:
            tenant.status = payload.status

        self.tenant_repo.commit()
        self.tenant_repo.refresh(tenant)
        return tenant

    def delete_tenant(self, tenant_id: str):
        tenant = self.get_tenant(tenant_id)

        # 若租户下仍有用户，阻止删除，避免外键/非空约束错误
        user_count = self.user_repo.count_by_tenant(tenant_id)
        if user_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="租户下仍有用户，请先删除或转移用户后再删除租户",
            )

        self.tenant_repo.delete(tenant)
        self.tenant_repo.commit()

    def update_status(self, tenant_id: str, status_value: bool) -> Tenant:
        tenant = self.get_tenant(tenant_id)
        tenant.status = status_value
        self.tenant_repo.commit()
        self.tenant_repo.refresh(tenant)
        return tenant

    def _create_tenant_admin_role(self, tenant_id: str) -> Optional[Role]:
        """为租户创建默认的租户管理员角色并分配权限
        
        注意：租户管理员角色是系统级角色，tenant_id为None
        """
        if not self.role_repo or not self.permission_repo:
            return None
        
        # 检查是否已存在租户管理员角色（系统级角色，tenant_id为None）
        existing_role = self.role_repo.get_by_name_in_tenant(None, "租户管理员")
        if existing_role:
            # 已存在角色，检查并更新权限（确保包含配置管理权限）
            import logging
            logger = logging.getLogger(__name__)
            
            # 获取当前角色的权限代码集合
            current_permission_codes = {perm.code for perm in existing_role.permissions} if existing_role.permissions else set()
            
            # 检查是否需要添加配置管理权限
            config_permissions_needed = {
                "system:config:menu",
                "system:config:read",
                "system:config:update",
            }
            
            if not config_permissions_needed.issubset(current_permission_codes):
                # 需要添加配置管理权限
                permissions_to_add = []
                for code in config_permissions_needed:
                    if code not in current_permission_codes:
                        permission = self.permission_repo.get_by_code(code)
                        if permission:
                            permissions_to_add.append(permission)
                
                if permissions_to_add:
                    # 添加新权限（保留现有权限）
                    if existing_role.permissions:
                        existing_role.permissions.extend(permissions_to_add)
                    else:
                        existing_role.permissions = permissions_to_add
                    # 不在这里commit，由主事务统一管理
                    logger.info(f"为已存在的租户管理员角色添加了 {len(permissions_to_add)} 个配置管理权限")
            
            return existing_role  # 已存在，返回现有角色
        
        # 创建租户管理员角色（系统级角色，tenant_id为None）
        admin_role = Role(
            tenant_id=None,  # 租户管理员角色是系统级角色，没有所属租户
            name="租户管理员",
            description="租户管理员角色，可以管理租户内的用户、角色、权限",
            status=True,
        )
        self.role_repo.add(admin_role)
        self.role_repo.flush()  # 获取角色ID
        
        # 获取所有租户级权限（tenant_id为None的系统级权限，以及该租户的权限）
        # 租户管理员需要的权限：用户管理、角色管理、权限管理、配置管理
        tenant_admin_permission_codes = [
            "system:user:create",
            "system:user:read",
            "system:user:update",
            "system:user:delete",
            "system:user:assign_role",
            "system:role:create",
            "system:role:read",
            "system:role:update",
            "system:role:delete",
            "system:role:assign_permission",
            "system:role:assign_user",
            "system:permission:create",
            "system:permission:read",
            "system:permission:update",
            "system:permission:delete",
            # 配置管理
            "system:config:menu",
            "system:config:read",
            "system:config:update",
            # 审计日志
            "system:audit:read",
        ]
        
        # 查询这些权限
        permissions = []
        for code in tenant_admin_permission_codes:
            permission = self.permission_repo.get_by_code(code)
            if permission:
                # 检查权限是否属于该租户或系统级
                if permission.tenant_id is None or permission.tenant_id == tenant_id:
                    permissions.append(permission)
        
        # 为角色分配权限
        admin_role.permissions = permissions
        # 不在这里commit，由主事务统一管理
        return admin_role

