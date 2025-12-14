"""
文档版本模型
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class DocumentVersion(Base):
    """文档版本实体"""
    __tablename__ = "document_versions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), comment="版本ID")
    document_id = Column(String, ForeignKey("documents.id"), nullable=False, comment="文档ID")
    version = Column(String(20), nullable=False, comment="版本号（V1, V2...）")
    file_hash = Column(String(64), nullable=False, comment="文件哈希值")
    storage_path = Column(String(1000), nullable=False, comment="存储路径")
    markdown_path = Column(String(1000), nullable=True, comment="Markdown路径")
    operator_id = Column(String, ForeignKey("users.id"), nullable=False, comment="操作者ID")
    remark = Column(String(500), nullable=True, comment="备注")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间")
    is_current = Column(Boolean, default=False, nullable=False, comment="是否为当前版本")
    
    # 关系
    document = relationship("Document", backref="versions")
    operator = relationship("User", foreign_keys=[operator_id])
    
    # 索引
    __table_args__ = (
        Index("idx_version_document", "document_id"),
        Index("idx_version_current", "is_current"),
    )

