"""
文档Chunk模型
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class DocumentChunk(Base):
    """文档Chunk实体（向量化后的文本片段）"""
    __tablename__ = "document_chunks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), comment="Chunk ID")
    document_id = Column(String, ForeignKey("documents.id"), nullable=False, comment="文档ID")
    folder_id = Column(String, ForeignKey("folders.id"), nullable=True, comment="文件夹ID（可为空，根目录文档）")
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, comment="租户ID")
    user_id = Column(String, ForeignKey("users.id"), nullable=False, comment="用户ID")
    chunk_index = Column(Integer, nullable=False, comment="Chunk索引（从0开始）")
    content = Column(Text, nullable=False, comment="Chunk文本内容")
    vector_id = Column(String(255), nullable=True, comment="向量库中的向量ID")
    chunk_metadata = Column(JSON, nullable=True, comment="元数据（JSON格式）")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间")
    
    # 关系
    document = relationship("Document", backref="chunks")
    folder = relationship("Folder", backref="chunks")
    
    # 索引
    __table_args__ = (
        Index("idx_chunk_document", "document_id"),
        Index("idx_chunk_folder", "folder_id"),
        Index("idx_chunk_tenant_user", "tenant_id", "user_id"),
        Index("idx_chunk_vector_id", "vector_id"),
    )

