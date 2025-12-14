"""
用户最近配置模型
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class UserRecentConfig(Base):
    """用户最近配置实体（每个用户只有一个最近配置）"""
    __tablename__ = "user_recent_configs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), comment="配置ID")
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True, comment="用户ID")
    chunk_size = Column(Integer, nullable=False, default=400, comment="文本切分块大小")
    chunk_overlap = Column(Integer, nullable=False, default=100, comment="文本切分重叠大小")
    split_method = Column(String(20), nullable=False, default="length", comment="切分方法：length/paragraph/keyword")
    split_keyword = Column(String(100), nullable=True, comment="切分关键字（当split_method=keyword时使用）")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")
    
    # 唯一约束：每个用户只有一个最近配置
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_recent_config"),
        Index("idx_recent_config_user", "user_id"),
    )

