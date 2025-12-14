"""
文档任务模型（待办表）
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index, Text, JSON
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class DocumentTask(Base):
    """文档任务实体（解析/向量化失败待办表）"""
    __tablename__ = "document_tasks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), comment="任务ID")
    document_id = Column(String, ForeignKey("documents.id"), nullable=False, comment="文档ID")
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, comment="租户ID")
    user_id = Column(String, ForeignKey("users.id"), nullable=False, comment="用户ID")
    task_type = Column(String(50), nullable=False, comment="任务类型：parse_failed/vectorize_failed")
    reason = Column(Text, nullable=True, comment="失败原因")
    retries = Column(Integer, nullable=False, default=0, comment="重试次数")
    task_data = Column(JSON, nullable=True, comment="任务数据（JSON格式，用于区分任务类型）")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")
    
    # 索引
    __table_args__ = (
        Index("idx_task_document", "document_id"),
        Index("idx_task_tenant_user", "tenant_id", "user_id"),
        Index("idx_task_type", "task_type"),
        Index("idx_task_created", "created_at"),
    )

