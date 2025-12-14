"""
文档标签关联模型
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class DocumentTagAssociation(Base):
    """文档标签关联实体"""
    __tablename__ = "document_tag_associations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), comment="关联ID")
    document_id = Column(String, ForeignKey("documents.id"), nullable=False, comment="文档ID")
    tag_id = Column(String, ForeignKey("document_tags.id"), nullable=False, comment="标签ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间")
    
    # 关系
    document = relationship("Document", backref="tag_associations")
    tag = relationship("DocumentTag", backref="document_associations")
    
    # 唯一约束：同一文档不能重复添加相同标签
    __table_args__ = (
        UniqueConstraint("document_id", "tag_id", name="uq_doc_tag"),
        Index("idx_assoc_document", "document_id"),
        Index("idx_assoc_tag", "tag_id"),
    )

