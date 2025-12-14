"""
文档配置模型
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class DocumentConfig(Base):
    """文档配置实体（文件-配置一对一）"""
    __tablename__ = "document_configs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), comment="配置ID")
    document_id = Column(String, ForeignKey("documents.id"), nullable=False, unique=True, comment="文档ID（一对一）")
    chunk_size = Column(Integer, nullable=False, default=400, comment="文本切分块大小（默认400）")
    chunk_overlap = Column(Integer, nullable=False, default=100, comment="文本切分重叠大小（默认100）")
    split_method = Column(String(20), nullable=False, default="length", comment="切分方法：length/paragraph/keyword")
    split_keyword = Column(String(100), nullable=True, comment="切分关键字（当split_method=keyword时使用）")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")
    
    # 关系
    document = relationship("Document", backref="config", uselist=False)
    
    # 索引
    __table_args__ = (
        Index("idx_config_document", "document_id"),
    )

