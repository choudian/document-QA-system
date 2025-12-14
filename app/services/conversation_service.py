"""
会话服务
"""
import logging
import json
from typing import Optional, Dict, Any, List
from app.repositories.conversation_repository import ConversationRepository
from app.models.conversation import Conversation
from app.core.exceptions import ConversationNotFoundException, ConversationPermissionDeniedException

logger = logging.getLogger(__name__)


class ConversationService:
    """会话应用服务层"""
    
    def __init__(self, conversation_repo: ConversationRepository):
        self.conversation_repo = conversation_repo
    
    def create_conversation(
        self,
        tenant_id: str,
        user_id: str,
        title: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """创建会话"""
        conversation = Conversation(
            tenant_id=tenant_id,
            user_id=user_id,
            title=title,
            status="active",
            config=json.dumps(config) if config else None
        )
        return self.conversation_repo.create(conversation)
    
    def get_conversation(self, conversation_id: str, tenant_id: str, user_id: str) -> Conversation:
        """获取会话详情"""
        conversation = self.conversation_repo.get_by_id(conversation_id, tenant_id)
        if not conversation:
            raise ConversationNotFoundException(conversation_id)
        
        if conversation.user_id != user_id:
            raise ConversationPermissionDeniedException(conversation_id)
        
        return conversation
    
    def list_conversations(
        self,
        user_id: str,
        tenant_id: str,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Conversation]:
        """查询会话列表"""
        return self.conversation_repo.list_by_user(user_id, tenant_id, status, skip, limit)
    
    def update_conversation(
        self,
        conversation_id: str,
        tenant_id: str,
        user_id: str,
        title: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """更新会话"""
        conversation = self.get_conversation(conversation_id, tenant_id, user_id)
        
        if title is not None:
            conversation.title = title
        if config is not None:
            conversation.config = json.dumps(config)
        
        return self.conversation_repo.update(conversation)
    
    def delete_conversation(self, conversation_id: str, tenant_id: str, user_id: str) -> bool:
        """删除会话"""
        conversation = self.get_conversation(conversation_id, tenant_id, user_id)
        return self.conversation_repo.delete(conversation_id)
    
    def archive_conversation(self, conversation_id: str, tenant_id: str, user_id: str) -> Conversation:
        """归档会话"""
        conversation = self.get_conversation(conversation_id, tenant_id, user_id)
        conversation.status = "archived"
        return self.conversation_repo.update(conversation)
    
    def get_conversation_config(self, conversation: Conversation) -> Dict[str, Any]:
        """获取会话配置"""
        if conversation.config:
            return json.loads(conversation.config)
        return {}
