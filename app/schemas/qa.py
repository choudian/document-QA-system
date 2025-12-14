"""
问答模块Schema定义
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# 会话相关Schema
class ConversationCreate(BaseModel):
    """创建会话请求"""
    title: Optional[str] = Field(None, description="会话标题")
    knowledge_base_ids: Optional[List[str]] = Field(None, description="知识库（文件夹）ID列表")
    top_k: Optional[int] = Field(None, description="检索top K个结果", ge=1, le=200)
    similarity_threshold: Optional[float] = Field(None, description="相似度阈值", ge=0, le=1)
    use_rerank: Optional[bool] = Field(False, description="是否使用重排序")
    rerank_top_n: Optional[int] = Field(None, description="重排序后的top N", ge=1, le=50)


class ConversationUpdate(BaseModel):
    """更新会话请求"""
    title: Optional[str] = Field(None, description="会话标题")
    knowledge_base_ids: Optional[List[str]] = Field(None, description="知识库（文件夹）ID列表")
    top_k: Optional[int] = Field(None, description="检索top K个结果", ge=1, le=200)
    similarity_threshold: Optional[float] = Field(None, description="相似度阈值", ge=0, le=1)
    use_rerank: Optional[bool] = Field(None, description="是否使用重排序")
    rerank_top_n: Optional[int] = Field(None, description="重排序后的top N", ge=1, le=50)


class ConversationResponse(BaseModel):
    """会话响应"""
    id: str
    tenant_id: str
    user_id: str
    title: Optional[str]
    status: str
    config: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# 消息相关Schema
class MessageResponse(BaseModel):
    """消息响应"""
    id: str
    conversation_id: str
    role: str
    content: str
    references: Optional[List[Dict[str, Any]]]
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]
    total_tokens: Optional[int]
    sequence: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    """消息列表响应"""
    messages: List[MessageResponse]
    total: int


# 对话相关Schema
class ChatRequest(BaseModel):
    """对话请求"""
    query: str = Field(..., description="用户问题", min_length=1)
    knowledge_base_ids: Optional[List[str]] = Field(None, description="知识库（文件夹）ID列表（可选，使用会话配置或默认）")
    top_k: Optional[int] = Field(None, description="检索top K个结果", ge=1, le=200)
    similarity_threshold: Optional[float] = Field(None, description="相似度阈值", ge=0, le=1)
    use_rerank: Optional[bool] = Field(False, description="是否使用重排序")
    rerank_top_n: Optional[int] = Field(None, description="重排序后的top N", ge=1, le=50)


class ChatResponse(BaseModel):
    """对话响应"""
    message_id: str
    content: str
    references: List[Dict[str, Any]]
    usage: Dict[str, Any]
