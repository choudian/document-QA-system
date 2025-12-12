"""
权限仓储
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.permission import Permission


class PermissionRepository:
    def __init__(self, db: Session):
        self.db = db

    # 查询
    def get(self, permission_id: str) -> Optional[Permission]:
        return self.db.query(Permission).filter(Permission.id == permission_id).first()

    def get_by_code(self, code: str) -> Optional[Permission]:
        return self.db.query(Permission).filter(Permission.code == code).first()

    def list(
        self,
        skip: int = 0,
        limit: int = 100,
        tenant_id: Optional[str] = None,
        module: Optional[str] = None,
        type: Optional[str] = None,
        status: Optional[bool] = None,
    ) -> List[Permission]:
        """查询权限列表，支持按租户、模块、类型、状态过滤"""
        query = self.db.query(Permission)
        
        if tenant_id is not None:
            # 如果指定了租户ID，只查询该租户的权限
            query = query.filter(Permission.tenant_id == tenant_id)
        elif tenant_id is False:
            # 如果tenant_id为False，只查询系统级权限
            query = query.filter(Permission.tenant_id.is_(None))
        
        if module is not None:
            query = query.filter(Permission.module == module)
        
        if type is not None:
            query = query.filter(Permission.type == type)
        
        if status is not None:
            query = query.filter(Permission.status == status)
        
        return query.offset(skip).limit(limit).all()

    def count(
        self,
        tenant_id: Optional[str] = None,
        module: Optional[str] = None,
        type: Optional[str] = None,
        status: Optional[bool] = None,
    ) -> int:
        """统计权限数量"""
        query = self.db.query(Permission)
        
        if tenant_id is not None:
            # 如果指定了租户ID，只查询该租户的权限
            query = query.filter(Permission.tenant_id == tenant_id)
        elif tenant_id is False:
            # 如果tenant_id为False，只查询系统级权限
            query = query.filter(Permission.tenant_id.is_(None))
        
        if module is not None:
            query = query.filter(Permission.module == module)
        
        if type is not None:
            query = query.filter(Permission.type == type)
        
        if status is not None:
            query = query.filter(Permission.status == status)
        
        return query.count()

    # 写入
    def add(self, permission: Permission):
        self.db.add(permission)

    def delete(self, permission: Permission):
        self.db.delete(permission)

    def flush(self):
        self.db.flush()

    def commit(self):
        self.db.commit()

    def rollback(self):
        self.db.rollback()

    def refresh(self, permission: Permission):
        self.db.refresh(permission)

