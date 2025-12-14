"""
文档标签Repository
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.models.document_tag import DocumentTag
from app.models.document_tag_association import DocumentTagAssociation


class DocumentTagRepository:
    """文档标签数据访问层"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_tag(self, tag: DocumentTag) -> DocumentTag:
        """创建标签"""
        self.db.add(tag)
        self.db.commit()
        self.db.refresh(tag)
        return tag
    
    def get_tag_by_id(self, tag_id: str) -> Optional[DocumentTag]:
        """根据ID查询标签"""
        return self.db.query(DocumentTag).filter(
            DocumentTag.id == tag_id
        ).first()
    
    def get_tag_by_name(self, name: str, user_id: str, tenant_id: str) -> Optional[DocumentTag]:
        """根据名称查询标签（同一用户下）"""
        return self.db.query(DocumentTag).filter(
            DocumentTag.tenant_id == tenant_id,
            DocumentTag.user_id == user_id,
            DocumentTag.name == name
        ).first()
    
    def list_tags_by_user(self, user_id: str, tenant_id: str, search: Optional[str] = None) -> List[DocumentTag]:
        """查询用户的标签列表（用于自动补全）"""
        query = self.db.query(DocumentTag).filter(
            DocumentTag.tenant_id == tenant_id,
            DocumentTag.user_id == user_id
        )
        if search:
            query = query.filter(DocumentTag.name.ilike(f"%{search}%"))
        return query.order_by(DocumentTag.created_at.desc()).all()
    
    def get_or_create_tag(self, name: str, user_id: str, tenant_id: str) -> DocumentTag:
        """获取或创建标签"""
        tag = self.get_tag_by_name(name, user_id, tenant_id)
        if tag:
            return tag
        
        tag = DocumentTag(
            tenant_id=tenant_id,
            user_id=user_id,
            name=name[:20]  # 限制20字
        )
        return self.create_tag(tag)
    
    def add_tag_to_document(self, document_id: str, tag_id: str) -> DocumentTagAssociation:
        """为文档添加标签"""
        # 检查是否已存在
        existing = self.db.query(DocumentTagAssociation).filter(
            DocumentTagAssociation.document_id == document_id,
            DocumentTagAssociation.tag_id == tag_id
        ).first()
        
        if existing:
            return existing
        
        association = DocumentTagAssociation(
            document_id=document_id,
            tag_id=tag_id
        )
        self.db.add(association)
        self.db.commit()
        self.db.refresh(association)
        return association
    
    def remove_tag_from_document(self, document_id: str, tag_id: str) -> bool:
        """从文档移除标签"""
        association = self.db.query(DocumentTagAssociation).filter(
            DocumentTagAssociation.document_id == document_id,
            DocumentTagAssociation.tag_id == tag_id
        ).first()
        
        if association:
            self.db.delete(association)
            self.db.commit()
            return True
        return False
    
    def get_document_tags(self, document_id: str) -> List[DocumentTag]:
        """获取文档的所有标签"""
        return self.db.query(DocumentTag).join(
            DocumentTagAssociation,
            DocumentTag.id == DocumentTagAssociation.tag_id
        ).filter(
            DocumentTagAssociation.document_id == document_id
        ).all()
    
    def search_documents_by_tag(self, tag_name: str, user_id: str, tenant_id: str) -> List[str]:
        """根据标签搜索文档ID列表"""
        from app.models.document import Document
        
        return self.db.query(Document.id).join(
            DocumentTagAssociation,
            Document.id == DocumentTagAssociation.document_id
        ).join(
            DocumentTag,
            DocumentTagAssociation.tag_id == DocumentTag.id
        ).filter(
            Document.tenant_id == tenant_id,
            Document.user_id == user_id,
            Document.deleted_at.is_(None),
            DocumentTag.name.ilike(f"%{tag_name}%")
        ).all()

