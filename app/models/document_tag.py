"""
文档标签模型
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class DocumentTag(Base):
    """文档标签实体（标签属于用户）"""
    __tablename__ = "document_tags"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), comment="标签ID")
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, comment="租户ID")
    user_id = Column(String, ForeignKey("users.id"), nullable=False, comment="用户ID（标签属于用户）")
    name = Column(String(20), nullable=False, comment="标签名称（20字以内）")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间")
    
    # 唯一约束：同一用户下标签名唯一
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_tag_user_name"),
        Index("idx_tag_tenant_user", "tenant_id", "user_id"),
    )

