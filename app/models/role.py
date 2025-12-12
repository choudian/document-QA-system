"""
角色模型
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Table, Index, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid

# 角色-权限关联表
role_permission = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', String, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True, comment="角色ID"),
    Column('permission_id', String, ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True, comment="权限ID"),
    Index('idx_role_permission_role', 'role_id'),
    Index('idx_role_permission_permission', 'permission_id'),
)

# 用户-角色关联表
user_role = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', String, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True, comment="用户ID"),
    Column('role_id', String, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True, comment="角色ID"),
    Index('idx_user_role_user', 'user_id'),
    Index('idx_user_role_role', 'role_id'),
)


class Role(Base):
    """角色实体"""
    __tablename__ = "roles"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), comment="角色ID")
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=True, comment="租户ID，None表示系统级角色（如租户管理员）")
    name = Column(String(100), nullable=False, comment="角色名称")
    description = Column(String(500), nullable=True, comment="角色描述")
    status = Column(Boolean, default=True, nullable=False, comment="状态：True-启用，False-停用")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")
    created_by = Column(String, nullable=True, comment="创建人ID")
    
    # 关系
    tenant = relationship("Tenant", backref="roles")
    permissions = relationship("Permission", secondary=role_permission, backref="roles")
    users = relationship("User", secondary=user_role, back_populates="roles")
    
    # 唯一约束：租户内角色名称唯一（系统级角色按名称唯一）
    __table_args__ = (
        UniqueConstraint('tenant_id', 'name', name='uq_tenant_role_name'),
        Index('idx_role_tenant', 'tenant_id'),
        Index('idx_role_name', 'name'),
    )
    
    def __repr__(self):
        return f"<Role(id={self.id}, tenant_id={self.tenant_id}, name={self.name}, status={self.status})>"

