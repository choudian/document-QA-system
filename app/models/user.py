"""
用户模型
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class User(Base):
    """用户实体"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), comment="用户ID")
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=True, comment="租户ID（系统管理员为空）")
    username = Column(String(50), nullable=False, comment="用户名")
    phone = Column(String(20), nullable=False, comment="手机号")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    status = Column(String(20), default="active", nullable=False, comment="状态：active-启用，frozen-冻结")
    is_tenant_admin = Column(Boolean, default=False, nullable=False, comment="是否为租户管理员")
    is_system_admin = Column(Boolean, default=False, nullable=False, comment="是否为系统管理员")
    mfa_enabled = Column(Boolean, default=False, nullable=False, comment="是否启用 MFA")
    mfa_secret = Column(String(255), nullable=True, comment="MFA 密钥（OTP secret）")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")
    created_by = Column(String, nullable=True, comment="创建人ID")
    
    # 唯一约束：tenant_id + username 唯一
    __table_args__ = (
        UniqueConstraint('tenant_id', 'username', name='uq_tenant_username'),
        UniqueConstraint('tenant_id', 'phone', name='uq_tenant_phone'),
        UniqueConstraint('phone', name='uq_user_phone_global'),
        Index('idx_tenant_id', 'tenant_id'),
        Index('idx_username', 'username'),
        Index('idx_phone', 'phone'),
    )
    
    # 关系
    tenant = relationship("Tenant", backref="users")
    roles = relationship("Role", secondary="user_roles", back_populates="users")
    
    def is_tenant_administrator(self) -> bool:
        """检查用户是否是租户管理员（通过角色判断）"""
        if not self.roles:
            return False
        return any(
            role.name == "租户管理员" and role.status and role.tenant_id is None
            for role in self.roles
        )
    
    def is_system_administrator(self) -> bool:
        """检查用户是否是系统管理员（通过角色判断）"""
        if not self.roles:
            return False
        return any(
            role.name == "系统管理员" and role.status and role.tenant_id is None
            for role in self.roles
        )
    
    def update_tenant_admin_status(self):
        """根据角色自动更新 is_tenant_admin 字段"""
        self.is_tenant_admin = self.is_tenant_administrator()
    
    def __repr__(self):
        return f"<User(id={self.id}, tenant_id={self.tenant_id}, username={self.username}, status={self.status})>"

