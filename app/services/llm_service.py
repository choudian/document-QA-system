"""
LLM服务 - 基于LangChain实现
"""
import logging
import json
import base64
from typing import Dict, Any, List, Optional, AsyncGenerator
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from app.services.config_service import ConfigService
from app.repositories.config_repository import ConfigRepository

logger = logging.getLogger(__name__)


class LLMService:
    """LLM服务 - 基于LangChain"""
    
    def __init__(self, config_service: ConfigService, config_repo: Optional[ConfigRepository] = None):
        self.config_service = config_service
        self.config_repo = config_repo
    
    def get_llm_config(self, tenant_id: Optional[str], user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取LLM配置（系统/租户/用户级），包含未脱敏的API key
        
        Args:
            tenant_id: 租户ID
            user_id: 用户ID（可选，用于获取用户级配置）
            
        Returns:
            LLM配置字典（包含真实的API key）
        """
        # 如果有config_repo，直接获取未脱敏的配置
        if self.config_repo:
            # 先尝试获取用户级配置
            if user_id:
                configs = self.config_repo.list_user_configs(user_id)
                for cfg in configs:
                    if cfg.category == "llm" and cfg.key == "default":
                        value = json.loads(cfg.value)
                        # 解密敏感字段
                        if "api_key" in value and isinstance(value["api_key"], str):
                            value["api_key"] = self._decrypt(value["api_key"])
                        return value
            
            # 尝试获取租户级配置
            if tenant_id:
                configs = self.config_repo.list_system_configs(tenant_id)
                for cfg in configs:
                    if cfg.category == "llm" and cfg.key == "default":
                        value = json.loads(cfg.value)
                        # 解密敏感字段
                        if "api_key" in value and isinstance(value["api_key"], str):
                            value["api_key"] = self._decrypt(value["api_key"])
                        return value
            
            # 使用系统默认配置
            configs = self.config_repo.list_system_configs(None)
            for cfg in configs:
                if cfg.category == "llm" and cfg.key == "default":
                    value = json.loads(cfg.value)
                    # 解密敏感字段
                    if "api_key" in value and isinstance(value["api_key"], str):
                        value["api_key"] = self._decrypt(value["api_key"])
                    return value
        
        # 如果没有config_repo，使用config_service（可能包含脱敏值）
        effective_config = self.config_service.get_effective_config(tenant_id, user_id)
        llm_config = effective_config.get("llm", {}).get("default")
        
        if not llm_config:
            raise ValueError("未找到LLM配置")
        
        return llm_config
    
    def _decrypt(self, text: str) -> str:
        """解密配置值"""
        if text.startswith("ENC:"):
            try:
                return base64.b64decode(text[4:].encode("utf-8")).decode("utf-8")
            except Exception:
                return text
        return text
    
    def _convert_messages(self, messages: List[Dict[str, str]]) -> List[BaseMessage]:
        """将消息列表转换为LangChain消息格式"""
        langchain_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "user":
                langchain_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
            else:
                # 未知角色，默认为用户消息
                langchain_messages.append(HumanMessage(content=content))
        
        return langchain_messages
    
    def _create_chat_model(self, config: Dict[str, Any], temperature: Optional[float] = None, 
                          max_tokens: Optional[int] = None, streaming: bool = False) -> ChatOpenAI:
        """创建ChatOpenAI实例"""
        base_url = config.get("base_url", "https://api.openai.com/v1")
        api_key = config.get("api_key", "")
        model = config.get("model", "gpt-4o-mini")
        config_temperature = config.get("temperature", 0.7)
        timeout = config.get("timeout", 60)
        
        # 解密API key
        if api_key.startswith("ENC:"):
            api_key = self._decrypt(api_key)
        
        # 构建ChatOpenAI参数
        # LangChain ChatOpenAI支持自定义base_url和api_key
        chat_params = {
            "model": model,
            "api_key": api_key,
            "base_url": base_url,  # 支持自定义API端点（如阿里云等OpenAI兼容API）
            "temperature": temperature if temperature is not None else config_temperature,
            "timeout": timeout,
            "streaming": streaming,
        }
        
        if max_tokens:
            chat_params["max_tokens"] = max_tokens
        
        return ChatOpenAI(**chat_params)
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        调用LLM进行对话（非流式）
        
        Args:
            messages: 消息列表，格式：[{"role": "user", "content": "..."}, ...]
            tenant_id: 租户ID
            user_id: 用户ID
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否流式输出（这里用于非流式调用，忽略）
        
        Returns:
            包含回复和token统计的字典
        """
        config = self.get_llm_config(tenant_id, user_id)
        
        # 转换为LangChain消息格式
        langchain_messages = self._convert_messages(messages)
        
        # 创建ChatOpenAI实例
        chat_model = self._create_chat_model(config, temperature, max_tokens, streaming=False)
        
        try:
            # 调用LangChain
            response = await chat_model.ainvoke(langchain_messages)
            
            # 获取usage信息（如果有）
            usage_info = {}
            if hasattr(response, "response_metadata"):
                metadata = response.response_metadata
                if "token_usage" in metadata:
                    token_usage = metadata["token_usage"]
                    usage_info = {
                        "prompt_tokens": token_usage.get("prompt_tokens", 0),
                        "completion_tokens": token_usage.get("completion_tokens", 0),
                        "total_tokens": token_usage.get("total_tokens", 0),
                    }
            
            return {
                "content": response.content if hasattr(response, "content") else str(response),
                "role": "assistant",
                "finish_reason": "stop",
                "usage": usage_info
            }
        except Exception as e:
            logger.error(f"LLM调用失败: {e}", exc_info=True)
            raise
    
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """
        调用LLM进行对话（流式输出）
        
        Args:
            messages: 消息列表
            tenant_id: 租户ID
            user_id: 用户ID
            temperature: 温度参数
            max_tokens: 最大token数
        
        Yields:
            SSE格式的字符串片段
        """
        config = self.get_llm_config(tenant_id, user_id)
        
        # 转换为LangChain消息格式
        langchain_messages = self._convert_messages(messages)
        
        # 创建ChatOpenAI实例（流式）
        chat_model = self._create_chat_model(config, temperature, max_tokens, streaming=True)
        
        try:
            # 使用astream进行流式调用
            async for chunk in chat_model.astream(langchain_messages):
                # chunk是AIMessageChunk类型
                if hasattr(chunk, "content") and chunk.content:
                    # 构建SSE格式的数据
                    chunk_data = {
                        "id": f"chatcmpl-{id(chunk)}",
                        "object": "chat.completion.chunk",
                        "created": 0,
                        "model": config.get("model", "gpt-4o-mini"),
                        "choices": [{
                            "index": 0,
                            "delta": {"content": chunk.content},
                            "finish_reason": None
                        }]
                    }
                    chunk_json = json.dumps(chunk_data, ensure_ascii=False)
                    yield f"data: {chunk_json}\n\n"
            
            # 流式完成
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"LLM流式调用失败: {e}", exc_info=True)
            # 发送错误信息
            error_data = {"error": str(e)}
            error_json = json.dumps(error_data, ensure_ascii=False)
            yield f"data: {error_json}\n\n"
            raise
