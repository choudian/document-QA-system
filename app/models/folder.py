"""
文件夹模型
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional
from app.core.database import Base
import uuid


class Folder(Base):
    """文件夹实体（领域模型）"""
    __tablename__ = "folders"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), comment="文件夹ID")
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, comment="租户ID")
    user_id = Column(String, ForeignKey("users.id"), nullable=False, comment="用户ID（拥有者）")
    parent_id = Column(String, ForeignKey("folders.id"), nullable=True, comment="父文件夹ID（可为空，表示根目录）")
    name = Column(String(255), nullable=False, comment="文件夹名称")
    path = Column(String(1000), nullable=False, comment="文件夹路径（租户id+用户id+文件夹层级id）")
    level = Column(Integer, nullable=False, default=0, comment="层级深度（0=根目录，最大2）")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")
    deleted_at = Column(DateTime(timezone=True), nullable=True, comment="软删除时间")
    
    # 关系
    parent = relationship("Folder", remote_side=[id], backref="children")
    
    # 索引
    __table_args__ = (
        Index("idx_folder_tenant_user", "tenant_id", "user_id"),
        Index("idx_folder_parent", "parent_id"),
        Index("idx_folder_deleted", "deleted_at"),
    )
    
    # 领域方法
    
    MAX_LEVEL = 1  # 最大层级（0=根目录，1=1级，共2层）
    
    def is_root(self) -> bool:
        """判断是否为根目录"""
        return self.level == 0
    
    def is_deleted(self) -> bool:
        """判断文件夹是否已删除"""
        return self.deleted_at is not None
    
    def is_owned_by(self, user_id: str) -> bool:
        """判断文件夹是否属于指定用户"""
        return self.user_id == user_id
    
    def can_create_subfolder(self) -> bool:
        """判断是否可以创建子文件夹"""
        return self.level < self.MAX_LEVEL
    
    def calculate_child_level(self) -> int:
        """计算子文件夹的层级"""
        if not self.can_create_subfolder():
            raise ValueError(f"文件夹层级已达到最大限制（{self.MAX_LEVEL}）")
        return self.level + 1
    
    def generate_child_path(self) -> str:
        """生成子文件夹路径"""
        return f"{self.path}/{self.id}"
    
    def rename(self, new_name: str) -> None:
        """重命名文件夹"""
        if not new_name or not new_name.strip():
            raise ValueError("文件夹名称不能为空")
        self.name = new_name.strip()
    
    def soft_delete(self) -> None:
        """软删除文件夹"""
        self.deleted_at = datetime.utcnow()
    
    def restore(self) -> None:
        """恢复文件夹"""
        self.deleted_at = None

