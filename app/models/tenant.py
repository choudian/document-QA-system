"""
租户模型
"""
from sqlalchemy import Column, String, Boolean, DateTime, Integer
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class Tenant(Base):
    """租户实体"""
    __tablename__ = "tenants"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), comment="租户ID")
    code = Column(String(50), nullable=False, unique=True, comment="租户编码")
    name = Column(String(100), nullable=False, unique=True, comment="租户名称")
    status = Column(Boolean, default=True, nullable=False, comment="状态：True-启用，False-停用")
    description = Column(String(500), nullable=True, comment="描述")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")
    created_by = Column(String, nullable=True, comment="创建人ID")
    
    def __repr__(self):
        return f"<Tenant(id={self.id}, name={self.name}, status={self.status})>"

