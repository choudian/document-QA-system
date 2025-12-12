"""
权限领域服务
"""
from typing import Optional, List
from fastapi import HTTPException, status
from app.models.permission import Permission
from app.schemas.permission import PermissionCreate, PermissionUpdate
from app.repositories.permission_repository import PermissionRepository


class PermissionService:
    def __init__(self, permission_repo: PermissionRepository):
        self.permission_repo = permission_repo

    def create_permission(self, permission: PermissionCreate) -> Permission:
        """创建权限"""
        # 检查权限码是否已存在
        existing = self.permission_repo.get_by_code(permission.code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"权限码 '{permission.code}' 已存在",
            )

        db_permission = Permission(
            code=permission.code,
            name=permission.name,
            description=permission.description,
            type=permission.type,
            module=permission.module,
            tenant_id=permission.tenant_id,
            status=permission.status,
        )

        try:
            self.permission_repo.add(db_permission)
            self.permission_repo.commit()
            self.permission_repo.refresh(db_permission)
            return db_permission
        except Exception as e:
            self.permission_repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"创建权限失败: {str(e)}",
            )

    def list_permissions(
        self,
        skip: int = 0,
        limit: int = 100,
        tenant_id: Optional[str] = None,
        module: Optional[str] = None,
        type: Optional[str] = None,
        status_filter: Optional[bool] = None,
    ) -> List[Permission]:
        """查询权限列表"""
        return self.permission_repo.list(
            skip=skip,
            limit=limit,
            tenant_id=tenant_id,
            module=module,
            type=type,
            status=status_filter,
        )

    def get_permission(self, permission_id: str) -> Permission:
        """获取权限详情"""
        permission = self.permission_repo.get(permission_id)
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"权限 ID '{permission_id}' 不存在",
            )
        return permission

    def update_permission(self, permission_id: str, payload: PermissionUpdate) -> Permission:
        """更新权限"""
        permission = self.get_permission(permission_id)

        # 如果更新权限码，检查新权限码是否已存在
        if payload.code and payload.code != permission.code:
            existing = self.permission_repo.get_by_code(payload.code)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"权限码 '{payload.code}' 已存在",
                )
            permission.code = payload.code

        if payload.name is not None:
            permission.name = payload.name
        if payload.description is not None:
            permission.description = payload.description
        if payload.type is not None:
            permission.type = payload.type
        if payload.module is not None:
            permission.module = payload.module
        if payload.status is not None:
            permission.status = payload.status

        try:
            self.permission_repo.commit()
            self.permission_repo.refresh(permission)
            return permission
        except Exception as e:
            self.permission_repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"更新权限失败: {str(e)}",
            )

    def delete_permission(self, permission_id: str):
        """删除权限"""
        permission = self.get_permission(permission_id)
        
        try:
            self.permission_repo.delete(permission)
            self.permission_repo.commit()
        except Exception as e:
            self.permission_repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"删除权限失败: {str(e)}",
            )

    def update_status(self, permission_id: str, status_value: bool) -> Permission:
        """更新权限状态"""
        permission = self.get_permission(permission_id)
        permission.status = status_value
        
        try:
            self.permission_repo.commit()
            self.permission_repo.refresh(permission)
            return permission
        except Exception as e:
            self.permission_repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"更新权限状态失败: {str(e)}",
            )

