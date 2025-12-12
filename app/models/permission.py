"""
权限模型
"""
from sqlalchemy import Column, String, Boolean, DateTime, Index
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class Permission(Base):
    """权限实体"""
    __tablename__ = "permissions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), comment="权限ID")
    code = Column(String(100), nullable=False, unique=True, comment="权限码（module:resource:action格式）")
    name = Column(String(100), nullable=False, comment="权限名称")
    description = Column(String(500), nullable=True, comment="权限描述")
    type = Column(String(20), nullable=False, comment="权限类型：menu-菜单，api-接口，button-按钮，tab-Tab页")
    module = Column(String(50), nullable=False, comment="所属模块")
    tenant_id = Column(String, nullable=True, comment="租户ID（为空表示系统级权限）")
    status = Column(Boolean, default=True, nullable=False, comment="状态：True-启用，False-停用")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")
    created_by = Column(String, nullable=True, comment="创建人ID")
    
    # 索引
    __table_args__ = (
        Index('idx_permission_code', 'code'),
        Index('idx_permission_tenant', 'tenant_id'),
        Index('idx_permission_module', 'module'),
        Index('idx_permission_type', 'type'),
    )
    
    def __repr__(self):
        return f"<Permission(id={self.id}, code={self.code}, name={self.name}, type={self.type})>"

