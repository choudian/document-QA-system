"""
消息Repository
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from app.models.message import Message


class MessageRepository:
    """消息数据访问层"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, message: Message) -> Message:
        """创建消息"""
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message
    
    def get_by_id(self, message_id: str, tenant_id: Optional[str] = None) -> Optional[Message]:
        """根据ID查询消息"""
        query = self.db.query(Message).filter(
            Message.id == message_id,
            Message.deleted_at.is_(None)
        )
        if tenant_id:
            query = query.filter(Message.tenant_id == tenant_id)
        return query.first()
    
    def list_by_conversation(
        self,
        conversation_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Message]:
        """查询会话的消息列表（按sequence排序）"""
        return self.db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.deleted_at.is_(None)
        ).order_by(Message.sequence).offset(skip).limit(limit).all()
    
    def get_next_sequence(self, conversation_id: str) -> int:
        """获取会话的下一个sequence序号"""
        last_message = self.db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.deleted_at.is_(None)
        ).order_by(desc(Message.sequence)).first()
        
        if last_message:
            return last_message.sequence + 1
        return 1
    
    def update(self, message: Message) -> Message:
        """更新消息"""
        self.db.commit()
        self.db.refresh(message)
        return message
    
    def delete(self, message_id: str) -> bool:
        """软删除消息"""
        message = self.get_by_id(message_id)
        if message:
            from datetime import datetime
            message.deleted_at = datetime.utcnow()
            self.db.commit()
            return True
        return False
    
    def count_by_conversation(self, conversation_id: str) -> int:
        """统计会话的消息数量"""
        return self.db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.deleted_at.is_(None)
        ).count()
