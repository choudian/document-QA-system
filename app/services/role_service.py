"""
角色领域服务
"""
from typing import Optional, List
from fastapi import HTTPException, status
from app.models.role import Role
from app.models.permission import Permission
from app.models.user import User
from app.schemas.role import RoleCreate, RoleUpdate, AssignPermissionsRequest, AssignRolesRequest, AssignUsersRequest
from app.repositories.role_repository import RoleRepository
from app.repositories.permission_repository import PermissionRepository
from app.repositories.user_repository import UserRepository


class RoleService:
    def __init__(
        self,
        role_repo: RoleRepository,
        permission_repo: PermissionRepository,
        user_repo: UserRepository,
    ):
        self.role_repo = role_repo
        self.permission_repo = permission_repo
        self.user_repo = user_repo

    def create_role(self, role: RoleCreate) -> Role:
        """创建角色"""
        # 检查租户内角色名称是否已存在
        existing = self.role_repo.get_by_name_in_tenant(role.tenant_id, role.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"租户内角色名称 '{role.name}' 已存在",
            )

        db_role = Role(
            tenant_id=role.tenant_id,
            name=role.name,
            description=role.description,
            status=role.status,
        )

        try:
            self.role_repo.add(db_role)
            self.role_repo.commit()
            self.role_repo.refresh(db_role)
            return db_role
        except Exception as e:
            self.role_repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"创建角色失败: {str(e)}",
            )

    def list_roles(
        self,
        skip: int = 0,
        limit: int = 100,
        tenant_id: Optional[str] = None,
        status_filter: Optional[bool] = None,
    ) -> List[Role]:
        """查询角色列表"""
        return self.role_repo.list(
            skip=skip,
            limit=limit,
            tenant_id=tenant_id,
            status=status_filter,
        )

    def get_role(self, role_id: str) -> Role:
        """获取角色详情"""
        role = self.role_repo.get(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"角色 ID '{role_id}' 不存在",
            )
        return role

    def update_role(self, role_id: str, payload: RoleUpdate) -> Role:
        """更新角色"""
        role = self.get_role(role_id)

        # 如果更新角色名称，检查新名称是否已存在
        if payload.name and payload.name != role.name:
            existing = self.role_repo.get_by_name_in_tenant(role.tenant_id, payload.name)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"租户内角色名称 '{payload.name}' 已存在",
                )
            role.name = payload.name

        if payload.description is not None:
            role.description = payload.description
        if payload.status is not None:
            role.status = payload.status

        try:
            self.role_repo.commit()
            self.role_repo.refresh(role)
            return role
        except Exception as e:
            self.role_repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"更新角色失败: {str(e)}",
            )

    def delete_role(self, role_id: str):
        """删除角色"""
        role = self.get_role(role_id)
        
        try:
            self.role_repo.delete(role)
            self.role_repo.commit()
        except Exception as e:
            self.role_repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"删除角色失败: {str(e)}",
            )

    def update_status(self, role_id: str, status_value: bool) -> Role:
        """更新角色状态"""
        role = self.get_role(role_id)
        role.status = status_value
        
        try:
            self.role_repo.commit()
            self.role_repo.refresh(role)
            return role
        except Exception as e:
            self.role_repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"更新角色状态失败: {str(e)}",
            )

    def assign_permissions(self, role_id: str, payload: AssignPermissionsRequest) -> Role:
        """为角色分配权限"""
        role = self.get_role(role_id)
        
        # 验证权限是否存在，并检查权限是否属于该租户或系统级
        permissions = []
        for permission_id in payload.permission_ids:
            permission = self.permission_repo.get(permission_id)
            if not permission:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"权限 ID '{permission_id}' 不存在",
                )
            # 检查权限是否属于该租户或系统级
            # 系统级角色（tenant_id为None）可以分配系统级权限或任何租户的权限
            # 租户级角色只能分配系统级权限或本租户的权限
            if role.tenant_id is not None:
                # 租户级角色：只能分配系统级权限或本租户的权限
                if permission.tenant_id is not None and permission.tenant_id != role.tenant_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"权限 '{permission.code}' 不属于该租户",
                    )
            # 系统级角色（tenant_id为None）可以分配任何权限，不需要检查
            permissions.append(permission)
        
        # 清空现有权限并分配新权限
        role.permissions = permissions
        
        try:
            self.role_repo.commit()
            self.role_repo.refresh(role)
            return role
        except Exception as e:
            self.role_repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"分配权限失败: {str(e)}",
            )

    def assign_roles_to_user(self, user_id: str, payload: AssignRolesRequest) -> User:
        """为用户分配角色"""
        user = self.user_repo.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"用户 ID '{user_id}' 不存在",
            )
        
        # 验证角色是否存在，并检查角色是否属于该用户的租户
        roles = []
        for role_id in payload.role_ids:
            role = self.role_repo.get(role_id)
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"角色 ID '{role_id}' 不存在",
                )
            # 检查角色是否属于该用户的租户
            # 系统级角色（tenant_id为None）可以分配给任何租户的用户
            # 租户级角色只能分配给本租户的用户
            if role.tenant_id is not None:
                # 租户级角色：只能分配给本租户的用户
                if user.tenant_id and role.tenant_id != user.tenant_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"角色 '{role.name}' 不属于该用户的租户",
                    )
            # 系统级角色（tenant_id为None）可以分配给任何租户的用户，不需要检查
            roles.append(role)
        
        # 清空现有角色并分配新角色
        user.roles = roles
        # 自动更新 is_tenant_admin 状态
        user.update_tenant_admin_status()
        
        try:
            self.user_repo.commit()
            self.user_repo.refresh(user)
            return user
        except Exception as e:
            self.user_repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"分配角色失败: {str(e)}",
            )

    def get_role_permissions(self, role_id: str) -> List[Permission]:
        """获取角色的权限列表"""
        role = self.get_role(role_id)
        return role.permissions

    def assign_users_to_role(self, role_id: str, payload: AssignUsersRequest) -> Role:
        """为角色分配用户"""
        from sqlalchemy.orm import joinedload
        
        # 使用 joinedload 预加载 users 关系
        role = (
            self.role_repo.db.query(Role)
            .options(joinedload(Role.users))
            .filter(Role.id == role_id)
            .first()
        )
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"角色 ID '{role_id}' 不存在",
            )
        
        # 验证用户是否存在，并检查用户是否属于该角色的租户
        users = []
        for user_id in payload.user_ids:
            user = self.user_repo.get(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"用户 ID '{user_id}' 不存在",
                )
            # 检查用户是否属于该角色的租户
            # 系统级角色（tenant_id为None）可以分配给任何租户的用户
            # 租户级角色只能分配给本租户的用户
            if role.tenant_id is not None:
                # 租户级角色：只能分配给本租户的用户
                if user.tenant_id != role.tenant_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"用户 '{user.username}' 不属于该角色的租户",
                    )
            # 系统级角色（tenant_id为None）可以分配给任何租户的用户，不需要检查
            users.append(user)
        
        # 清空现有用户并分配新用户
        role.users = users
        # 自动更新所有相关用户的 is_tenant_admin 状态
        for user in users:
            user.update_tenant_admin_status()
        
        try:
            self.role_repo.commit()
            # 刷新并重新加载 users 关系
            self.role_repo.db.refresh(role)
            # 重新查询以加载 users 关系
            role = (
                self.role_repo.db.query(Role)
                .options(joinedload(Role.users))
                .filter(Role.id == role_id)
                .first()
            )
            return role
        except Exception as e:
            self.role_repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"分配用户失败: {str(e)}",
            )

    def get_role_users(self, role_id: str) -> List[User]:
        """获取角色的用户列表"""
        from sqlalchemy.orm import joinedload
        
        # 使用 joinedload 预加载 users 关系
        role = (
            self.role_repo.db.query(Role)
            .options(joinedload(Role.users))
            .filter(Role.id == role_id)
            .first()
        )
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"角色 ID '{role_id}' 不存在",
            )
        return role.users

