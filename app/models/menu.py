"""
菜单模型
"""
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Index, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class Menu(Base):
    """菜单实体"""
    __tablename__ = "menus"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), comment="菜单ID")
    parent_id = Column(String, ForeignKey("menus.id", ondelete="CASCADE"), nullable=True, comment="父菜单ID")
    name = Column(String(100), nullable=False, comment="菜单名称")
    path = Column(String(200), nullable=True, comment="路由路径")
    icon = Column(String(50), nullable=True, comment="图标名称（Ant Design图标名称）")
    permission_code = Column(String(100), nullable=True, comment="关联的权限码（type='menu'的权限）")
    sort_order = Column(Integer, default=0, nullable=False, comment="排序序号")
    visible = Column(Boolean, default=True, nullable=False, comment="是否可见")
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=True, comment="租户ID（None表示系统级菜单）")
    status = Column(Boolean, default=True, nullable=False, comment="状态：True-启用，False-停用")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")
    created_by = Column(String, nullable=True, comment="创建人ID")
    
    # 关系
    parent = relationship("Menu", remote_side=[id], backref="children")
    tenant = relationship("Tenant", backref="menus")
    
    # 索引和约束
    __table_args__ = (
        Index('idx_menu_parent', 'parent_id'),
        Index('idx_menu_tenant', 'tenant_id'),
        Index('idx_menu_sort', 'sort_order'),
        Index('idx_menu_permission', 'permission_code'),
    )
    
    def __repr__(self):
        return f"<Menu(id={self.id}, name={self.name}, path={self.path}, tenant_id={self.tenant_id})>"

