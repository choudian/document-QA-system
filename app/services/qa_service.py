"""
问答服务
"""
import logging
import json
from typing import List, Dict, Any, Optional, AsyncGenerator
from app.services.retrieval_service import RetrievalService
from app.services.llm_service import LLMService
from app.services.conversation_service import ConversationService
from app.services.message_service import MessageService
from app.repositories.conversation_repository import ConversationRepository
from app.models.conversation import Conversation
from app.models.message import Message

logger = logging.getLogger(__name__)


class QAService:
    """问答服务"""
    
    def __init__(
        self,
        retrieval_service: RetrievalService,
        llm_service: LLMService,
        conversation_service: ConversationService,
        message_service: MessageService,
        conversation_repo: ConversationRepository
    ):
        self.retrieval_service = retrieval_service
        self.llm_service = llm_service
        self.conversation_service = conversation_service
        self.message_service = message_service
        self.conversation_repo = conversation_repo
    
    def _build_context_prompt(self, query: str, references: List[Dict[str, Any]]) -> str:
        """构建包含上下文的提示词"""
        if not references:
            return query
        
        # 构建上下文
        context_parts = []
        for i, ref in enumerate(references, 1):
            content = ref.get("content", "")
            document_id = ref.get("document_id", "")
            chunk_index = ref.get("chunk_index", 0)
            
            context_parts.append(f"[参考片段{i}] (文档: {document_id}, 片段: {chunk_index})\n{content}")
        
        context = "\n\n".join(context_parts)
        
        # 构建完整的提示词
        prompt = f"""请基于以下参考内容回答用户的问题。如果参考内容中没有相关信息，请说明无法从提供的资料中找到答案。

参考内容：
{context}

用户问题：{query}

请回答："""
        
        return prompt
    
    async def chat(
        self,
        conversation_id: str,
        query: str,
        tenant_id: str,
        user_id: str,
        knowledge_base_ids: Optional[List[str]] = None,
        top_k: int = 5,
        similarity_threshold: Optional[float] = None,
        use_rerank: bool = False,
        rerank_top_n: Optional[int] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        进行问答（非流式）
        
        Args:
            conversation_id: 会话ID
            query: 用户问题
            tenant_id: 租户ID
            user_id: 用户ID
            knowledge_base_ids: 知识库（文件夹）ID列表
            top_k: 检索top K个结果
            similarity_threshold: 相似度阈值
            use_rerank: 是否使用重排序
            rerank_top_n: 重排序后的top N
            stream: 是否流式输出
        
        Returns:
            包含回复、引用和token统计的字典
        """
        # 1. 获取会话（验证权限和配置）
        conversation = self.conversation_service.get_conversation(conversation_id, tenant_id, user_id)
        config = self.conversation_service.get_conversation_config(conversation)
        
        # 从会话配置中获取检索参数（如果配置了的话）
        if not knowledge_base_ids and "knowledge_base_ids" in config:
            knowledge_base_ids = config.get("knowledge_base_ids")
        if "top_k" in config:
            top_k = config.get("top_k", top_k)
        if "similarity_threshold" in config:
            similarity_threshold = config.get("similarity_threshold", similarity_threshold)
        if "use_rerank" in config:
            use_rerank = config.get("use_rerank", use_rerank)
        if "rerank_top_n" in config:
            rerank_top_n = config.get("rerank_top_n", rerank_top_n)
        
        # 2. 检索相关内容
        references = await self.retrieval_service.search(
            query=query,
            tenant_id=tenant_id,
            user_id=user_id,
            knowledge_base_ids=knowledge_base_ids,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
            use_rerank=use_rerank,
            rerank_top_n=rerank_top_n
        )
        
        # 3. 获取历史消息（用于构建上下文）
        history_messages = self.message_service.list_messages(
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            user_id=user_id,
            skip=0,
            limit=10  # 最近10条消息
        )
        
        # 4. 构建消息列表（用于LLM调用）
        messages = []
        
        # 添加系统消息（如果需要）
        # messages.append({"role": "system", "content": "你是一个智能助手，基于提供的参考内容回答问题。"})
        
        # 添加历史消息（最近N条）
        for msg in history_messages[-5:]:  # 只取最近5条
            if msg.role in ["user", "assistant"]:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # 构建当前问题的提示词（包含检索到的上下文）
        context_prompt = self._build_context_prompt(query, references)
        messages.append({"role": "user", "content": context_prompt})
        
        # 5. 调用LLM生成回复
        llm_response = await self.llm_service.chat_completion(
            messages=messages,
            tenant_id=tenant_id,
            user_id=user_id,
            stream=False
        )
        
        # 6. 保存用户消息
        user_message = self.message_service.create_message(
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            user_id=user_id,
            role="user",
            content=query
        )
        
        # 7. 保存AI回复消息
        assistant_message = self.message_service.create_message(
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            user_id=user_id,
            role="assistant",
            content=llm_response["content"],
            references=references,
            prompt_tokens=llm_response.get("usage", {}).get("prompt_tokens"),
            completion_tokens=llm_response.get("usage", {}).get("completion_tokens"),
            total_tokens=llm_response.get("usage", {}).get("total_tokens")
        )
        
        # 8. 更新会话标题（如果还没有标题，使用第一个问题作为标题）
        if not conversation.title:
            conversation.title = query[:50]  # 最多50个字符
            self.conversation_repo.update(conversation)
        
        # 9. 返回结果
        return {
            "message_id": assistant_message.id,
            "content": llm_response["content"],
            "references": references,
            "usage": llm_response.get("usage", {})
        }
    
    async def chat_stream(
        self,
        conversation_id: str,
        query: str,
        tenant_id: str,
        user_id: str,
        knowledge_base_ids: Optional[List[str]] = None,
        top_k: int = 5,
        similarity_threshold: Optional[float] = None,
        use_rerank: bool = False,
        rerank_top_n: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """
        进行问答（流式输出）
        
        Args:
            conversation_id: 会话ID
            query: 用户问题
            tenant_id: 租户ID
            user_id: 用户ID
            knowledge_base_ids: 知识库（文件夹）ID列表
            top_k: 检索top K个结果
            similarity_threshold: 相似度阈值
            use_rerank: 是否使用重排序
            rerank_top_n: 重排序后的top N
        
        Yields:
            SSE格式的字符串片段
        """
        # 1. 获取会话（验证权限和配置）
        conversation = self.conversation_service.get_conversation(conversation_id, tenant_id, user_id)
        config = self.conversation_service.get_conversation_config(conversation)
        
        # 从会话配置中获取检索参数（如果配置了的话）
        if not knowledge_base_ids and "knowledge_base_ids" in config:
            knowledge_base_ids = config.get("knowledge_base_ids")
        if "top_k" in config:
            top_k = config.get("top_k", top_k)
        if "similarity_threshold" in config:
            similarity_threshold = config.get("similarity_threshold", similarity_threshold)
        if "use_rerank" in config:
            use_rerank = config.get("use_rerank", use_rerank)
        if "rerank_top_n" in config:
            rerank_top_n = config.get("rerank_top_n", rerank_top_n)
        
        # 2. 检索相关内容
        import json
        references = await self.retrieval_service.search(
            query=query,
            tenant_id=tenant_id,
            user_id=user_id,
            knowledge_base_ids=knowledge_base_ids,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
            use_rerank=use_rerank,
            rerank_top_n=rerank_top_n
        )
        
        # 发送引用信息（在流式输出开始前）
        yield f"data: {json.dumps({'type': 'references', 'references': references}, ensure_ascii=False)}\n\n"
        
        # 3. 获取历史消息
        history_messages = self.message_service.list_messages(
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            user_id=user_id,
            skip=0,
            limit=10
        )
        
        # 4. 构建消息列表
        messages = []
        for msg in history_messages[-5:]:
            if msg.role in ["user", "assistant"]:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # 构建当前问题的提示词
        context_prompt = self._build_context_prompt(query, references)
        messages.append({"role": "user", "content": context_prompt})
        
        # 5. 保存用户消息
        user_message = self.message_service.create_message(
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            user_id=user_id,
            role="user",
            content=query
        )
        
        # 6. 流式调用LLM
        full_content = ""
        async for chunk in self.llm_service.chat_completion_stream(
            messages=messages,
            tenant_id=tenant_id,
            user_id=user_id
        ):
            # 解析chunk（如果是SSE格式）
            if chunk.startswith("data: "):
                data_str = chunk[6:].strip()
                if data_str == "[DONE]":
                    # 流式输出完成，保存AI回复消息
                    assistant_message = self.message_service.create_message(
                        conversation_id=conversation_id,
                        tenant_id=tenant_id,
                        user_id=user_id,
                        role="assistant",
                        content=full_content,
                        references=references
                    )
                    
                    # 更新会话标题
                    if not conversation.title:
                        conversation.title = query[:50]
                        self.conversation_repo.update(conversation)
                    
                    yield chunk
                    break
                
                # 如果不是 [DONE]，继续处理并累积内容
                try:
                    data_json = json.loads(data_str)
                    # 提取content
                    if "choices" in data_json and len(data_json["choices"]) > 0:
                        delta = data_json["choices"][0].get("delta", {})
                        if "content" in delta:
                            full_content += delta["content"]
                except json.JSONDecodeError:
                    pass
            
            yield chunk
