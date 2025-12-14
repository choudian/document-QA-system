"""
问答API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.api.v1.me import get_current_user
from app.schemas.qa import (
    ConversationCreate, ConversationUpdate, ConversationResponse,
    MessageResponse, MessageListResponse,
    ChatRequest, ChatResponse
)
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.folder_repository import FolderRepository
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.config_repository import ConfigRepository
from app.services.conversation_service import ConversationService
from app.services.message_service import MessageService
from app.services.retrieval_service import RetrievalService
from app.services.reranker_service import RerankerService
from app.services.llm_service import LLMService
from app.services.qa_service import QAService
from app.services.embedding_service import EmbeddingService
from app.services.config_service import ConfigService
from app.core.permissions import require_permission
from app.models.user import User

router = APIRouter()


def _build_qa_service(db: Session) -> QAService:
    """构建问答服务"""
    config_repo = ConfigRepository(db)
    config_service = ConfigService(config_repo)
    
    conversation_repo = ConversationRepository(db)
    message_repo = MessageRepository(db)
    folder_repo = FolderRepository(db)
    chunk_repo = DocumentChunkRepository(db)
    document_repo = DocumentRepository(db)
    
    conversation_service = ConversationService(conversation_repo)
    message_service = MessageService(message_repo, conversation_repo)
    
    embedding_service = EmbeddingService(config_service, config_repo)
    reranker_service = RerankerService(config_service, config_repo)
    retrieval_service = RetrievalService(
        embedding_service=embedding_service,
        config_service=config_service,
        folder_repo=folder_repo,
        chunk_repo=chunk_repo,
        document_repo=document_repo,
        reranker_service=reranker_service
    )
    
    llm_service = LLMService(config_service, config_repo)
    
    qa_service = QAService(
        retrieval_service=retrieval_service,
        llm_service=llm_service,
        conversation_service=conversation_service,
        message_service=message_service,
        conversation_repo=conversation_repo
    )
    
    return qa_service


def _build_conversation_service(db: Session) -> ConversationService:
    """构建会话服务"""
    conversation_repo = ConversationRepository(db)
    return ConversationService(conversation_repo)


def _build_message_service(db: Session) -> MessageService:
    """构建消息服务"""
    conversation_repo = ConversationRepository(db)
    message_repo = MessageRepository(db)
    return MessageService(message_repo, conversation_repo)


# 会话管理接口
@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    conversation: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(require_permission("qa:conversation:create"))
):
    """创建会话"""
    service = _build_conversation_service(db)
    
    # 构建会话配置
    config = {}
    if conversation.knowledge_base_ids:
        config["knowledge_base_ids"] = conversation.knowledge_base_ids
    if conversation.top_k is not None:
        config["top_k"] = conversation.top_k
    if conversation.similarity_threshold is not None:
        config["similarity_threshold"] = conversation.similarity_threshold
    if conversation.use_rerank is not None:
        config["use_rerank"] = conversation.use_rerank
    if conversation.rerank_top_n is not None:
        config["rerank_top_n"] = conversation.rerank_top_n
    
    created = service.create_conversation(
        tenant_id=current_user.tenant_id or "",
        user_id=current_user.id,
        title=conversation.title,
        config=config if config else None
    )
    
    import json
    response_data = {
        "id": created.id,
        "tenant_id": created.tenant_id,
        "user_id": created.user_id,
        "title": created.title,
        "status": created.status,
        "config": json.loads(created.config) if created.config else None,
        "created_at": created.created_at,
        "updated_at": created.updated_at
    }
    return ConversationResponse(**response_data)


@router.get("/conversations", response_model=List[ConversationResponse])
def list_conversations(
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(require_permission("qa:conversation:read"))
):
    """查询会话列表"""
    service = _build_conversation_service(db)
    import json
    conversations = service.list_conversations(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id or "",
        status=status_filter,
        skip=skip,
        limit=limit
    )
    
    result = []
    for c in conversations:
        response_data = {
            "id": c.id,
            "tenant_id": c.tenant_id,
            "user_id": c.user_id,
            "title": c.title,
            "status": c.status,
            "config": json.loads(c.config) if c.config else None,
            "created_at": c.created_at,
            "updated_at": c.updated_at
        }
        result.append(ConversationResponse(**response_data))
    return result


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(require_permission("qa:conversation:read"))
):
    """查询会话详情"""
    import json
    service = _build_conversation_service(db)
    conversation = service.get_conversation(
        conversation_id=conversation_id,
        tenant_id=current_user.tenant_id or "",
        user_id=current_user.id
    )
    
    # 构建响应（需要解析config JSON）
    response_data = {
        "id": conversation.id,
        "tenant_id": conversation.tenant_id,
        "user_id": conversation.user_id,
        "title": conversation.title,
        "status": conversation.status,
        "config": json.loads(conversation.config) if conversation.config else None,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at
    }
    return ConversationResponse(**response_data)


@router.put("/conversations/{conversation_id}", response_model=ConversationResponse)
def update_conversation(
    conversation_id: str,
    conversation: ConversationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(require_permission("qa:conversation:update"))
):
    """更新会话"""
    service = _build_conversation_service(db)
    
    # 构建配置更新
    config = None
    config_dict = {}
    if conversation.knowledge_base_ids is not None:
        config_dict["knowledge_base_ids"] = conversation.knowledge_base_ids
    if conversation.top_k is not None:
        config_dict["top_k"] = conversation.top_k
    if conversation.similarity_threshold is not None:
        config_dict["similarity_threshold"] = conversation.similarity_threshold
    if conversation.use_rerank is not None:
        config_dict["use_rerank"] = conversation.use_rerank
    if conversation.rerank_top_n is not None:
        config_dict["rerank_top_n"] = conversation.rerank_top_n
    
    if config_dict:
        config = config_dict
    
    import json
    updated = service.update_conversation(
        conversation_id=conversation_id,
        tenant_id=current_user.tenant_id or "",
        user_id=current_user.id,
        title=conversation.title,
        config=config
    )
    
    response_data = {
        "id": updated.id,
        "tenant_id": updated.tenant_id,
        "user_id": updated.user_id,
        "title": updated.title,
        "status": updated.status,
        "config": json.loads(updated.config) if updated.config else None,
        "created_at": updated.created_at,
        "updated_at": updated.updated_at
    }
    return ConversationResponse(**response_data)


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(require_permission("qa:conversation:delete"))
):
    """删除会话"""
    service = _build_conversation_service(db)
    service.delete_conversation(
        conversation_id=conversation_id,
        tenant_id=current_user.tenant_id or "",
        user_id=current_user.id
    )
    return None


@router.post("/conversations/{conversation_id}/archive", response_model=ConversationResponse)
def archive_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(require_permission("qa:conversation:update"))
):
    """归档会话"""
    service = _build_conversation_service(db)
    import json
    archived = service.archive_conversation(
        conversation_id=conversation_id,
        tenant_id=current_user.tenant_id or "",
        user_id=current_user.id
    )
    
    response_data = {
        "id": archived.id,
        "tenant_id": archived.tenant_id,
        "user_id": archived.user_id,
        "title": archived.title,
        "status": archived.status,
        "config": json.loads(archived.config) if archived.config else None,
        "created_at": archived.created_at,
        "updated_at": archived.updated_at
    }
    return ConversationResponse(**response_data)


# 消息管理接口
@router.get("/conversations/{conversation_id}/messages", response_model=MessageListResponse)
def list_messages(
    conversation_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(require_permission("qa:message:read"))
):
    """查询会话的消息列表"""
    service = _build_message_service(db)
    messages = service.list_messages(
        conversation_id=conversation_id,
        tenant_id=current_user.tenant_id or "",
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    
    from app.repositories.message_repository import MessageRepository
    message_repo = MessageRepository(db)
    total = message_repo.count_by_conversation(conversation_id)
    
    return MessageListResponse(
        messages=[MessageResponse.from_orm(m) for m in messages],
        total=total
    )


@router.get("/messages/{message_id}", response_model=MessageResponse)
def get_message(
    message_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(require_permission("qa:message:read"))
):
    """查询消息详情"""
    service = _build_message_service(db)
    message = service.get_message(
        message_id=message_id,
        tenant_id=current_user.tenant_id or "",
        user_id=current_user.id
    )
    return MessageResponse.from_orm(message)


@router.delete("/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(
    message_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(require_permission("qa:message:delete"))
):
    """删除消息"""
    service = _build_message_service(db)
    service.delete_message(
        message_id=message_id,
        tenant_id=current_user.tenant_id or "",
        user_id=current_user.id
    )
    return None


# 对话接口
@router.post("/conversations/{conversation_id}/chat", response_model=ChatResponse)
async def chat(
    conversation_id: str,
    chat_request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(require_permission("qa:conversation:chat"))
):
    """进行问答（非流式）"""
    service = _build_qa_service(db)
    
    result = await service.chat(
        conversation_id=conversation_id,
        query=chat_request.query,
        tenant_id=current_user.tenant_id or "",
        user_id=current_user.id,
        knowledge_base_ids=chat_request.knowledge_base_ids,
        top_k=chat_request.top_k or 5,
        similarity_threshold=chat_request.similarity_threshold,
        use_rerank=chat_request.use_rerank or False,
        rerank_top_n=chat_request.rerank_top_n,
        stream=False
    )
    
    return ChatResponse(**result)


@router.post("/conversations/{conversation_id}/chat/stream")
async def chat_stream(
    conversation_id: str,
    chat_request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(require_permission("qa:conversation:chat"))
):
    """进行问答（流式输出）"""
    service = _build_qa_service(db)
    
    async def generate():
        async for chunk in service.chat_stream(
            conversation_id=conversation_id,
            query=chat_request.query,
            tenant_id=current_user.tenant_id or "",
            user_id=current_user.id,
            knowledge_base_ids=chat_request.knowledge_base_ids,
            top_k=chat_request.top_k or 5,
            similarity_threshold=chat_request.similarity_threshold,
            use_rerank=chat_request.use_rerank or False,
            rerank_top_n=chat_request.rerank_top_n
        ):
            yield chunk
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
