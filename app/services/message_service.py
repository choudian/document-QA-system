"""
消息服务
"""
import logging
import json
from typing import Optional, Dict, Any, List
from app.repositories.message_repository import MessageRepository
from app.repositories.conversation_repository import ConversationRepository
from app.models.message import Message
from app.core.exceptions import MessageNotFoundException, MessagePermissionDeniedException

logger = logging.getLogger(__name__)


class MessageService:
    """消息应用服务层"""
    
    def __init__(
        self,
        message_repo: MessageRepository,
        conversation_repo: ConversationRepository
    ):
        self.message_repo = message_repo
        self.conversation_repo = conversation_repo
    
    def create_message(
        self,
        conversation_id: str,
        tenant_id: str,
        user_id: str,
        role: str,
        content: str,
        references: Optional[List[Dict[str, Any]]] = None,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        total_tokens: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """创建消息"""
        # 获取下一个sequence
        sequence = self.message_repo.get_next_sequence(conversation_id)
        
        message = Message(
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            user_id=user_id,
            role=role,
            content=content,
            references=references,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            metadata=metadata,
            sequence=sequence
        )
        return self.message_repo.create(message)
    
    def get_message(self, message_id: str, tenant_id: str, user_id: str) -> Message:
        """获取消息详情"""
        message = self.message_repo.get_by_id(message_id, tenant_id)
        if not message:
            raise MessageNotFoundException(message_id)
        
        # 验证会话权限（消息属于会话，通过会话验证权限）
        conversation = self.conversation_repo.get_by_id(message.conversation_id, tenant_id)
        if not conversation or conversation.user_id != user_id:
            raise MessagePermissionDeniedException(message_id)
        
        return message
    
    def list_messages(
        self,
        conversation_id: str,
        tenant_id: str,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Message]:
        """查询会话的消息列表"""
        # 验证会话权限
        conversation = self.conversation_repo.get_by_id(conversation_id, tenant_id)
        if not conversation or conversation.user_id != user_id:
            raise MessagePermissionDeniedException(conversation_id)
        
        return self.message_repo.list_by_conversation(conversation_id, skip, limit)
    
    def delete_message(self, message_id: str, tenant_id: str, user_id: str) -> bool:
        """删除消息"""
        message = self.get_message(message_id, tenant_id, user_id)
        return self.message_repo.delete(message_id)
