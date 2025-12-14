"""
文档模型
"""
from sqlalchemy import Column, String, Integer, BigInteger, DateTime, ForeignKey, Index, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional
from app.core.database import Base
from app.core.value_objects import DocumentStatus
import uuid


class Document(Base):
    """文档实体（领域模型）"""
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), comment="文档ID")
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, comment="租户ID")
    user_id = Column(String, ForeignKey("users.id"), nullable=False, comment="用户ID（拥有者）")
    folder_id = Column(String, ForeignKey("folders.id"), nullable=True, comment="所属文件夹ID（可为空）")
    name = Column(String(255), nullable=False, comment="文件名")
    original_name = Column(String(255), nullable=False, comment="原始文件名")
    file_type = Column(String(20), nullable=False, comment="文件类型（txt/md/pdf/word）")
    mime_type = Column(String(100), nullable=False, comment="MIME类型")
    file_size = Column(BigInteger, nullable=False, comment="文件大小（字节）")
    file_hash = Column(String(64), nullable=False, comment="文件哈希值（SHA256，用于去重）")
    storage_path = Column(String(1000), nullable=False, comment="存储路径（原文件）")
    markdown_path = Column(String(1000), nullable=True, comment="Markdown解析结果路径")
    version = Column(String(20), nullable=False, default="V1", comment="版本号（V1, V2...）")
    status = Column(String(20), nullable=False, default="uploading", comment="状态：uploading/uploaded/parsing/completed/upload_failed/parse_failed")
    page_count = Column(Integer, nullable=True, comment="页数（PDF/Word）")
    title = Column(String(500), nullable=True, comment="文档标题（解析后提取）")
    summary = Column(Text, nullable=True, comment="摘要（解析后提取）")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")
    deleted_at = Column(DateTime(timezone=True), nullable=True, comment="软删除时间")
    
    # 关系
    folder = relationship("Folder", backref="documents")
    
    # 索引
    __table_args__ = (
        Index("idx_document_tenant_user", "tenant_id", "user_id"),
        Index("idx_document_folder", "folder_id"),
        Index("idx_document_status", "status"),
        Index("idx_document_deleted", "deleted_at"),
        Index("idx_document_hash", "file_hash"),
    )
    
    # 领域方法
    
    def is_processing(self) -> bool:
        """判断文档是否正在处理中"""
        return DocumentStatus.is_processing(self.status)
    
    def is_failed(self) -> bool:
        """判断文档是否处理失败"""
        return DocumentStatus.is_failed(self.status)
    
    def is_deleted(self) -> bool:
        """判断文档是否已删除"""
        return self.deleted_at is not None
    
    def is_owned_by(self, user_id: str) -> bool:
        """判断文档是否属于指定用户"""
        return self.user_id == user_id
    
    def can_be_deleted(self) -> bool:
        """判断文档是否可以删除（不在处理中）"""
        return not self.is_processing()
    
    def mark_as_parsing(self) -> None:
        """标记为解析中"""
        self.status = DocumentStatus.PARSING.value
    
    def mark_as_vectorizing(self) -> None:
        """标记为向量化中"""
        self.status = DocumentStatus.VECTORIZING.value
    
    def mark_as_completed(self) -> None:
        """标记为已完成"""
        self.status = DocumentStatus.COMPLETED.value
    
    def mark_as_parse_failed(self) -> None:
        """标记为解析失败"""
        self.status = DocumentStatus.PARSE_FAILED.value
    
    def mark_as_vectorize_failed(self) -> None:
        """标记为向量化失败"""
        self.status = DocumentStatus.VECTORIZE_FAILED.value
    
    def soft_delete(self) -> None:
        """软删除文档"""
        self.deleted_at = datetime.utcnow()
    
    def restore(self) -> None:
        """恢复文档"""
        self.deleted_at = None
    
    def update_parsing_result(self, markdown_path: str, title: Optional[str] = None, summary: Optional[str] = None, page_count: Optional[int] = None) -> None:
        """更新解析结果"""
        self.markdown_path = markdown_path
        if title:
            self.title = title[:500]  # 限制长度
        if summary:
            self.summary = summary
        if page_count is not None:
            self.page_count = page_count

