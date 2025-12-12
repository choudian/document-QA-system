"""
用户仓储
"""
from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_username_in_tenant(self, tenant_id: str, username: str) -> Optional[User]:
        return (
            self.db.query(User)
            .filter(User.tenant_id == tenant_id, User.username == username)
            .first()
        )

    def get_by_phone_in_tenant(self, tenant_id: str, phone: str) -> Optional[User]:
        return (
            self.db.query(User)
            .filter(User.tenant_id == tenant_id, User.phone == phone)
            .first()
        )

    def count_by_tenant(self, tenant_id: str) -> int:
        return self.db.query(User).filter(User.tenant_id == tenant_id).count()

    def get_system_admin_by_phone(self, phone: str) -> Optional[User]:
        return (
            self.db.query(User)
            .filter(User.is_system_admin == True, User.phone == phone)
            .first()
        )

    def has_system_admin(self) -> bool:
        return self.db.query(User).filter(User.is_system_admin == True).first() is not None

    def get(self, user_id: str) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_phone(self, phone: str) -> Optional[User]:
        return self.db.query(User).filter(User.phone == phone).first()

    def add(self, user: User):
        self.db.add(user)

    def flush(self):
        self.db.flush()

    def commit(self):
        self.db.commit()

    def rollback(self):
        self.db.rollback()

    def refresh(self, user: User):
        self.db.refresh(user)

