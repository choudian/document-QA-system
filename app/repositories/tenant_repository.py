"""
租户仓储
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.tenant import Tenant


class TenantRepository:
    def __init__(self, db: Session):
        self.db = db

    # 查询
    def get(self, tenant_id: str) -> Optional[Tenant]:
        return self.db.query(Tenant).filter(Tenant.id == tenant_id).first()

    def get_by_code(self, code: str) -> Optional[Tenant]:
        return self.db.query(Tenant).filter(Tenant.code == code).first()

    def get_by_name(self, name: str) -> Optional[Tenant]:
        return self.db.query(Tenant).filter(Tenant.name == name).first()

    def list(self, skip: int = 0, limit: int = 100, status: Optional[bool] = None) -> List[Tenant]:
        query = self.db.query(Tenant)
        if status is not None:
            query = query.filter(Tenant.status == status)
        return query.offset(skip).limit(limit).all()

    # 写入
    def add(self, tenant: Tenant):
        self.db.add(tenant)

    def delete(self, tenant: Tenant):
        self.db.delete(tenant)

    def flush(self):
        self.db.flush()

    def commit(self):
        self.db.commit()

    def rollback(self):
        self.db.rollback()

    def refresh(self, tenant: Tenant):
        self.db.refresh(tenant)

