"""
角色仓储
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.role import Role


class RoleRepository:
    def __init__(self, db: Session):
        self.db = db

    # 查询
    def get(self, role_id: str) -> Optional[Role]:
        return self.db.query(Role).filter(Role.id == role_id).first()

    def get_by_name_in_tenant(self, tenant_id: Optional[str], name: str) -> Optional[Role]:
        """根据租户ID和名称查询角色，tenant_id为None时查询系统级角色"""
        if tenant_id is None:
            return (
                self.db.query(Role)
                .filter(Role.tenant_id.is_(None), Role.name == name)
                .first()
            )
        else:
            return (
                self.db.query(Role)
                .filter(Role.tenant_id == tenant_id, Role.name == name)
                .first()
            )

    def list(
        self,
        skip: int = 0,
        limit: int = 100,
        tenant_id: Optional[str] = None,
        status: Optional[bool] = None,
    ) -> List[Role]:
        """查询角色列表，支持按租户、状态过滤"""
        query = self.db.query(Role)
        
        if tenant_id is not None:
            # 如果指定了租户ID，只查询该租户的角色
            query = query.filter(Role.tenant_id == tenant_id)
        else:
            # tenant_id为None或False时，只查询系统级角色（tenant_id为None）
            query = query.filter(Role.tenant_id.is_(None))
        
        if status is not None:
            query = query.filter(Role.status == status)
        
        return query.offset(skip).limit(limit).all()

    def count(
        self,
        tenant_id: Optional[str] = None,
        status: Optional[bool] = None,
    ) -> int:
        """统计角色数量"""
        query = self.db.query(Role)
        
        if tenant_id is not None:
            # 如果指定了租户ID，只查询该租户的角色
            query = query.filter(Role.tenant_id == tenant_id)
        else:
            # tenant_id为None或False时，只查询系统级角色（tenant_id为None）
            query = query.filter(Role.tenant_id.is_(None))
        
        if status is not None:
            query = query.filter(Role.status == status)
        
        return query.count()

    # 写入
    def add(self, role: Role):
        self.db.add(role)

    def delete(self, role: Role):
        self.db.delete(role)

    def flush(self):
        self.db.flush()

    def commit(self):
        self.db.commit()

    def rollback(self):
        self.db.rollback()

    def refresh(self, role: Role):
        self.db.refresh(role)

