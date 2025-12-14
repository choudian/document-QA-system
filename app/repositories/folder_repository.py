"""
文件夹Repository
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.folder import Folder


class FolderRepository:
    """文件夹数据访问层"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, folder: Folder) -> Folder:
        """创建文件夹"""
        self.db.add(folder)
        self.db.commit()
        self.db.refresh(folder)
        return folder
    
    def get_by_id(self, folder_id: str, tenant_id: Optional[str] = None) -> Optional[Folder]:
        """根据ID查询文件夹"""
        query = self.db.query(Folder).filter(
            Folder.id == folder_id,
            Folder.deleted_at.is_(None)
        )
        if tenant_id:
            query = query.filter(Folder.tenant_id == tenant_id)
        return query.first()
    
    def list_by_user(self, user_id: str, tenant_id: str, parent_id: Optional[str] = None) -> List[Folder]:
        """查询用户的文件夹列表"""
        query = self.db.query(Folder).filter(
            Folder.tenant_id == tenant_id,
            Folder.user_id == user_id,
            Folder.deleted_at.is_(None)
        )
        if parent_id is None:
            query = query.filter(Folder.parent_id.is_(None))
        else:
            query = query.filter(Folder.parent_id == parent_id)
        return query.order_by(Folder.created_at.desc()).all()
    
    def get_by_path(self, path: str, tenant_id: str, user_id: str) -> Optional[Folder]:
        """根据路径查询文件夹"""
        return self.db.query(Folder).filter(
            Folder.tenant_id == tenant_id,
            Folder.user_id == user_id,
            Folder.path == path,
            Folder.deleted_at.is_(None)
        ).first()
    
    def check_name_exists(self, name: str, parent_id: Optional[str], tenant_id: str, user_id: str) -> bool:
        """检查文件夹名称是否已存在（在同一父文件夹下）"""
        query = self.db.query(Folder).filter(
            Folder.tenant_id == tenant_id,
            Folder.user_id == user_id,
            Folder.name == name,
            Folder.deleted_at.is_(None)
        )
        if parent_id is None:
            query = query.filter(Folder.parent_id.is_(None))
        else:
            query = query.filter(Folder.parent_id == parent_id)
        return query.first() is not None
    
    def update(self, folder: Folder) -> Folder:
        """更新文件夹"""
        self.db.commit()
        self.db.refresh(folder)
        return folder
    
    def delete(self, folder_id: str) -> bool:
        """软删除文件夹"""
        folder = self.get_by_id(folder_id)
        if folder:
            from datetime import datetime
            folder.deleted_at = datetime.utcnow()
            self.db.commit()
            return True
        return False
    
    def get_children_count(self, folder_id: str) -> int:
        """获取子文件夹数量"""
        return self.db.query(Folder).filter(
            Folder.parent_id == folder_id,
            Folder.deleted_at.is_(None)
        ).count()
    
    def get_max_level(self, tenant_id: str, user_id: str) -> int:
        """获取用户文件夹的最大层级"""
        result = self.db.query(Folder.level).filter(
            Folder.tenant_id == tenant_id,
            Folder.user_id == user_id,
            Folder.deleted_at.is_(None)
        ).order_by(Folder.level.desc()).first()
        return result[0] if result else 0

