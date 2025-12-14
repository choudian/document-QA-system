"""
文档版本Repository
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.document_version import DocumentVersion


class DocumentVersionRepository:
    """文档版本数据访问层"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, version: DocumentVersion) -> DocumentVersion:
        """创建版本"""
        self.db.add(version)
        self.db.commit()
        self.db.refresh(version)
        return version
    
    def get_by_id(self, version_id: str) -> Optional[DocumentVersion]:
        """根据ID查询版本"""
        return self.db.query(DocumentVersion).filter(
            DocumentVersion.id == version_id
        ).first()
    
    def list_by_document(self, document_id: str) -> List[DocumentVersion]:
        """查询文档的所有版本"""
        return self.db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id
        ).order_by(desc(DocumentVersion.created_at)).all()
    
    def get_current_version(self, document_id: str) -> Optional[DocumentVersion]:
        """获取文档的当前版本"""
        return self.db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id,
            DocumentVersion.is_current == True
        ).first()
    
    def set_current_version(self, document_id: str, version_id: str) -> bool:
        """设置当前版本"""
        # 先取消所有版本的当前标记
        self.db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id
        ).update({"is_current": False})
        
        # 设置新版本为当前版本
        version = self.get_by_id(version_id)
        if version:
            version.is_current = True
            self.db.commit()
            return True
        return False
    
    def delete(self, version_id: str) -> bool:
        """删除版本"""
        version = self.get_by_id(version_id)
        if version:
            # 不能删除当前版本
            if version.is_current:
                return False
            self.db.delete(version)
            self.db.commit()
            return True
        return False
    
    def get_next_version_number(self, document_id: str) -> str:
        """获取下一个版本号"""
        versions = self.list_by_document(document_id)
        if not versions:
            return "V1"
        
        # 提取最大版本号
        max_version = 0
        for version in versions:
            try:
                version_num = int(version.version.lstrip("V"))
                max_version = max(max_version, version_num)
            except ValueError:
                continue
        
        return f"V{max_version + 1}"

