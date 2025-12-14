"""
消息模型
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class Message(Base):
    """消息实体"""
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), comment="消息ID")
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False, comment="会话ID")
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, comment="租户ID")
    user_id = Column(String, ForeignKey("users.id"), nullable=False, comment="用户ID")
    
    # 消息角色：user（用户消息）、assistant（AI回复）、system（系统消息）
    role = Column(String(20), nullable=False, comment="消息角色：user/assistant/system")
    
    # 消息内容
    content = Column(Text, nullable=False, comment="消息内容")
    
    # 引用信息（JSON格式，存储向量检索结果）
    # 包含：文档ID、chunk索引、相似度分数、引用文本等
    references = Column(JSON, nullable=True, comment="引用信息（JSON格式，向量检索结果）")
    
    # Token统计
    prompt_tokens = Column(Integer, nullable=True, comment="提示词Token数量")
    completion_tokens = Column(Integer, nullable=True, comment="回复Token数量")
    total_tokens = Column(Integer, nullable=True, comment="总Token数量")
    
    # 元数据（JSON格式，存储额外的元数据）
    metadata = Column(JSON, nullable=True, comment="元数据（JSON格式）")
    
    # 排序序号（用于保持消息顺序）
    sequence = Column(Integer, nullable=False, comment="排序序号")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")
    deleted_at = Column(DateTime(timezone=True), nullable=True, comment="软删除时间")
    
    # 关系
    conversation = relationship("Conversation", backref="messages")
    user = relationship("User", backref="messages")
    tenant = relationship("Tenant", backref="messages")
    
    # 索引
    __table_args__ = (
        Index("idx_message_conversation", "conversation_id"),
        Index("idx_message_tenant_user", "tenant_id", "user_id"),
        Index("idx_message_sequence", "conversation_id", "sequence"),
        Index("idx_message_deleted", "deleted_at"),
    )
