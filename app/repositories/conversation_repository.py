"""
会话Repository
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from app.models.conversation import Conversation


class ConversationRepository:
    """会话数据访问层"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, conversation: Conversation) -> Conversation:
        """创建会话"""
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation
    
    def get_by_id(self, conversation_id: str, tenant_id: Optional[str] = None) -> Optional[Conversation]:
        """根据ID查询会话"""
        query = self.db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.deleted_at.is_(None)
        )
        if tenant_id:
            query = query.filter(Conversation.tenant_id == tenant_id)
        return query.first()
    
    def list_by_user(
        self,
        user_id: str,
        tenant_id: str,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Conversation]:
        """查询用户的会话列表"""
        query = self.db.query(Conversation).filter(
            Conversation.tenant_id == tenant_id,
            Conversation.user_id == user_id,
            Conversation.deleted_at.is_(None)
        )
        if status:
            query = query.filter(Conversation.status == status)
        return query.order_by(desc(Conversation.updated_at)).offset(skip).limit(limit).all()
    
    def update(self, conversation: Conversation) -> Conversation:
        """更新会话"""
        self.db.commit()
        self.db.refresh(conversation)
        return conversation
    
    def delete(self, conversation_id: str) -> bool:
        """软删除会话"""
        conversation = self.get_by_id(conversation_id)
        if conversation:
            from datetime import datetime
            conversation.deleted_at = datetime.utcnow()
            self.db.commit()
            return True
        return False
