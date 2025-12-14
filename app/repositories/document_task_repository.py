"""
文档任务数据访问层
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from app.models.document_task import DocumentTask


class DocumentTaskRepository:
    """文档任务数据访问层"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, task: DocumentTask) -> DocumentTask:
        """创建任务"""
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task
    
    def get_by_id(self, task_id: str) -> Optional[DocumentTask]:
        """根据ID查询任务"""
        return self.db.query(DocumentTask).filter(DocumentTask.id == task_id).first()
    
    def list_by_user(
        self,
        user_id: str,
        tenant_id: str,
        task_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[DocumentTask]:
        """查询用户的任务列表"""
        query = self.db.query(DocumentTask).filter(
            and_(
                DocumentTask.tenant_id == tenant_id,
                DocumentTask.user_id == user_id
            )
        )
        
        if task_type:
            query = query.filter(DocumentTask.task_type == task_type)
        
        return query.order_by(desc(DocumentTask.created_at)).offset(skip).limit(limit).all()
    
    def list_by_document(self, document_id: str) -> List[DocumentTask]:
        """查询文档的所有任务"""
        return self.db.query(DocumentTask).filter(
            DocumentTask.document_id == document_id
        ).order_by(desc(DocumentTask.created_at)).all()
    
    def delete(self, task_id: str) -> bool:
        """删除任务"""
        task = self.get_by_id(task_id)
        if task:
            self.db.delete(task)
            self.db.commit()
            return True
        return False
    
    def delete_by_document_id(self, document_id: str) -> int:
        """删除文档的所有任务"""
        count = self.db.query(DocumentTask).filter(
            DocumentTask.document_id == document_id
        ).delete()
        self.db.commit()
        return count

