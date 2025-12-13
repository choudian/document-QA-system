"""
配置相关模型
"""
from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class SystemConfig(Base):
    """系统/租户级配置"""

    __tablename__ = "system_configs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), comment="配置ID")
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=True, comment="租户ID，空表示系统级")
    category = Column(String(50), nullable=False, comment="配置类别")
    key = Column(String(100), nullable=False, comment="配置键")
    value = Column(Text, nullable=False, comment="配置值(JSON字符串)")
    status = Column(Boolean, default=True, nullable=False, comment="启用状态")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")
    created_by = Column(String, nullable=True, comment="创建人ID")

    __table_args__ = (
        UniqueConstraint("tenant_id", "category", "key", name="uq_system_config_scope_key"),
        Index("idx_system_config_tenant", "tenant_id"),
        Index("idx_system_config_category_key", "category", "key"),
    )

    def __repr__(self):
        return f"<SystemConfig(tenant_id={self.tenant_id}, {self.category}:{self.key})>"


class UserConfig(Base):
    """用户级配置"""

    __tablename__ = "user_configs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), comment="配置ID")
    user_id = Column(String, ForeignKey("users.id"), nullable=False, comment="用户ID")
    category = Column(String(50), nullable=False, comment="配置类别")
    key = Column(String(100), nullable=False, comment="配置键")
    value = Column(Text, nullable=False, comment="配置值(JSON字符串)")
    status = Column(Boolean, default=True, nullable=False, comment="启用状态")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")
    created_by = Column(String, nullable=True, comment="创建人ID")

    __table_args__ = (
        UniqueConstraint("user_id", "category", "key", name="uq_user_config_scope_key"),
        Index("idx_user_config_user", "user_id"),
        Index("idx_user_config_category_key", "category", "key"),
    )

    def __repr__(self):
        return f"<UserConfig(user_id={self.user_id}, {self.category}:{self.key})>"


class ConfigHistory(Base):
    """配置历史记录"""

    __tablename__ = "config_histories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), comment="记录ID")
    scope_type = Column(String(10), nullable=False, comment="作用域类型：system/tenant/user")
    scope_id = Column(String, nullable=True, comment="作用域ID（系统为空，租户ID或用户ID）")
    category = Column(String(50), nullable=False, comment="配置类别")
    key = Column(String(100), nullable=False, comment="配置键")
    old_value = Column(Text, nullable=True, comment="旧值(JSON字符串)")
    new_value = Column(Text, nullable=True, comment="新值(JSON字符串)")
    operator_id = Column(String, nullable=True, comment="操作人ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间")

    __table_args__ = (
        Index("idx_config_history_scope", "scope_type", "scope_id"),
        Index("idx_config_history_category_key", "category", "key"),
        Index("idx_config_history_created", "created_at"),
    )

    def __repr__(self):
        return f"<ConfigHistory({self.scope_type}:{self.scope_id}, {self.category}:{self.key})>"

