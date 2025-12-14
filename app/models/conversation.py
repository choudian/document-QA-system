"""
会话模型
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class Conversation(Base):
    """会话实体"""
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), comment="会话ID")
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, comment="租户ID")
    user_id = Column(String, ForeignKey("users.id"), nullable=False, comment="用户ID（拥有者）")
    title = Column(String(500), nullable=True, comment="会话标题（可选，可由第一条消息自动生成）")
    status = Column(String(20), nullable=False, default="active", comment="状态：active/archived/deleted")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")
    deleted_at = Column(DateTime(timezone=True), nullable=True, comment="软删除时间")
    
    # 会话配置（JSON格式存储）
    # 包含：knowledge_base_ids（知识库/文件夹ID列表）、top_k、similarity_threshold、use_rerank、rerank_top_n等
    config = Column(String(2000), nullable=True, comment="会话配置（JSON格式）")
    
    # 关系
    user = relationship("User", backref="conversations")
    tenant = relationship("Tenant", backref="conversations")
    
    # 索引
    __table_args__ = (
        Index("idx_conversation_tenant_user", "tenant_id", "user_id"),
        Index("idx_conversation_user", "user_id"),
        Index("idx_conversation_status", "status"),
        Index("idx_conversation_deleted", "deleted_at"),
    )
