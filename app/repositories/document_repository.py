"""
文档Repository
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from app.models.document import Document


class DocumentRepository:
    """文档数据访问层"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, document: Document) -> Document:
        """创建文档"""
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document
    
    def get_by_id(self, document_id: str, tenant_id: Optional[str] = None) -> Optional[Document]:
        """根据ID查询文档"""
        query = self.db.query(Document).filter(
            Document.id == document_id,
            Document.deleted_at.is_(None)
        )
        if tenant_id:
            query = query.filter(Document.tenant_id == tenant_id)
        return query.first()
    
    def list_by_user(
        self,
        user_id: str,
        tenant_id: str,
        folder_id: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Document]:
        """查询用户的文档列表"""
        query = self.db.query(Document).filter(
            Document.tenant_id == tenant_id,
            Document.user_id == user_id,
            Document.deleted_at.is_(None)
        )
        if folder_id is not None:
            query = query.filter(Document.folder_id == folder_id)
        if status:
            query = query.filter(Document.status == status)
        return query.order_by(desc(Document.created_at)).offset(skip).limit(limit).all()
    
    def check_duplicate(self, name: str, folder_id: Optional[str], tenant_id: str, user_id: str) -> Optional[Document]:
        """检查同名文件是否存在（在同一文件夹下）"""
        query = self.db.query(Document).filter(
            Document.tenant_id == tenant_id,
            Document.user_id == user_id,
            Document.name == name,
            Document.deleted_at.is_(None)
        )
        if folder_id is None:
            query = query.filter(Document.folder_id.is_(None))
        else:
            query = query.filter(Document.folder_id == folder_id)
        return query.first()
    
    def get_by_hash(self, file_hash: str, tenant_id: str) -> Optional[Document]:
        """根据文件哈希查询文档"""
        return self.db.query(Document).filter(
            Document.tenant_id == tenant_id,
            Document.file_hash == file_hash,
            Document.deleted_at.is_(None)
        ).first()
    
    def update(self, document: Document) -> Document:
        """更新文档"""
        self.db.commit()
        self.db.refresh(document)
        return document
    
    def delete(self, document_id: str) -> bool:
        """软删除文档（已废弃，使用Document.soft_delete()方法）"""
        document = self.get_by_id(document_id)
        if document:
            document.soft_delete()
            self.db.commit()
            return True
        return False
    
    def count_by_folder(self, folder_id: str) -> int:
        """统计文件夹下的文档数量"""
        return self.db.query(Document).filter(
            Document.folder_id == folder_id,
            Document.deleted_at.is_(None)
        ).count()

