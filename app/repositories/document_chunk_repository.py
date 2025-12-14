"""
文档Chunk Repository
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.document_chunk import DocumentChunk


class DocumentChunkRepository:
    """文档Chunk Repository"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, chunk: DocumentChunk) -> DocumentChunk:
        """创建chunk"""
        self.db.add(chunk)
        self.db.flush()
        return chunk
    
    def create_batch(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """批量创建chunk"""
        self.db.add_all(chunks)
        self.db.flush()
        return chunks
    
    def get_by_id(self, chunk_id: str) -> Optional[DocumentChunk]:
        """根据ID获取chunk"""
        return self.db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    
    def get_by_document_id(self, document_id: str) -> List[DocumentChunk]:
        """根据文档ID获取所有chunk"""
        return self.db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).order_by(DocumentChunk.chunk_index).all()
    
    def list_by_document(
        self,
        document_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[DocumentChunk]:
        """分页查询文档的chunk"""
        return self.db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).order_by(DocumentChunk.chunk_index).offset(skip).limit(limit).all()
    
    def delete_by_document_id(self, document_id: str) -> int:
        """根据文档ID删除所有chunk"""
        deleted = self.db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).delete()
        return deleted
    
    def delete_by_folder_id(self, folder_id: str) -> int:
        """根据文件夹ID删除所有chunk"""
        deleted = self.db.query(DocumentChunk).filter(
            DocumentChunk.folder_id == folder_id
        ).delete()
        return deleted
    
    def commit(self):
        """提交事务"""
        self.db.commit()
    
    def rollback(self):
        """回滚事务"""
        self.db.rollback()

