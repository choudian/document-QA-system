"""
LLM服务
"""
import logging
import json
import base64
from typing import Dict, Any, List, Optional, AsyncGenerator
import httpx
from app.services.config_service import ConfigService
from app.repositories.config_repository import ConfigRepository

logger = logging.getLogger(__name__)


class LLMService:
    """LLM服务"""
    
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
            stream: 是否流式输出（这里用于非流式调用）
        
        Returns:
            包含回复和token统计的字典
        """
        config = self.get_llm_config(tenant_id, user_id)
        return await self._chat_completion_with_config(
            messages, config, temperature, max_tokens, stream=False
        )
    
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
        async for chunk in self._chat_completion_stream_with_config(
            messages, config, temperature, max_tokens
        ):
            yield chunk
    
    async def _chat_completion_with_config(
        self,
        messages: List[Dict[str, str]],
        config: Dict[str, Any],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """使用指定配置调用LLM"""
        provider = config.get("provider", "openai")
        
        if provider == "openai" or provider == "aliyun":
            return await self._chat_completion_openai(
                messages, config, temperature, max_tokens, stream
            )
        else:
            raise ValueError(f"不支持的LLM provider: {provider}")
    
    async def _chat_completion_openai(
        self,
        messages: List[Dict[str, str]],
        config: Dict[str, Any],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """使用OpenAI兼容API进行对话"""
        base_url = config.get("base_url", "https://api.openai.com/v1")
        api_key = config.get("api_key", "")
        model = config.get("model", "gpt-4o-mini")
        config_temperature = config.get("temperature", 0.7)
        timeout = config.get("timeout", 60)
        
        # 解密API key
        if api_key.startswith("ENC:"):
            api_key = self._decrypt(api_key)
        
        url = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # 构建请求参数
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature if temperature is not None else config_temperature,
            "stream": stream
        }
        if max_tokens:
            data["max_tokens"] = max_tokens
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.post(url, headers=headers, json=data)
                response.raise_for_status()
                result = response.json()
                
                # 解析响应
                choice = result["choices"][0]
                message = choice["message"]
                
                return {
                    "content": message.get("content", ""),
                    "role": message.get("role", "assistant"),
                    "finish_reason": choice.get("finish_reason"),
                    "usage": result.get("usage", {})
                }
            except httpx.HTTPStatusError as e:
                error_detail = ""
                if e.response is not None:
                    try:
                        error_detail = e.response.json()
                    except:
                        error_detail = e.response.text[:500]
                logger.error(f"LLM API调用失败: {e.response.status_code if e.response else 'N/A'}, URL: {url}, Model: {model}, 错误详情: {error_detail}")
                raise
    
    async def _chat_completion_stream_with_config(
        self,
        messages: List[Dict[str, str]],
        config: Dict[str, Any],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """使用指定配置进行流式对话"""
        provider = config.get("provider", "openai")
        
        if provider == "openai" or provider == "aliyun":
            async for chunk in self._chat_completion_stream_openai(
                messages, config, temperature, max_tokens
            ):
                yield chunk
        else:
            raise ValueError(f"不支持的LLM provider: {provider}")
    
    async def _chat_completion_stream_openai(
        self,
        messages: List[Dict[str, str]],
        config: Dict[str, Any],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """使用OpenAI兼容API进行流式对话"""
        base_url = config.get("base_url", "https://api.openai.com/v1")
        api_key = config.get("api_key", "")
        model = config.get("model", "gpt-4o-mini")
        config_temperature = config.get("temperature", 0.7)
        timeout = config.get("timeout", 60)
        
        # 解密API key
        if api_key.startswith("ENC:"):
            api_key = self._decrypt(api_key)
        
        url = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # 构建请求参数
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature if temperature is not None else config_temperature,
            "stream": True
        }
        if max_tokens:
            data["max_tokens"] = max_tokens
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                async with client.stream("POST", url, headers=headers, json=data) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        
                        # OpenAI流式响应格式：data: {...} 或 data: [DONE]
                        if line.startswith("data: "):
                            data_str = line[6:]  # 去掉 "data: " 前缀
                            
                            if data_str == "[DONE]":
                                yield f"data: [DONE]\n\n"
                                break
                            
                            try:
                                data_json = json.loads(data_str)
                                # 发送SSE格式的数据
                                yield f"data: {json.dumps(data_json, ensure_ascii=False)}\n\n"
                            except json.JSONDecodeError:
                                logger.warning(f"无法解析流式响应数据: {data_str}")
                                continue
            except httpx.HTTPStatusError as e:
                error_detail = ""
                if e.response is not None:
                    try:
                        error_detail = e.response.json()
                    except:
                        error_detail = e.response.text[:500]
                logger.error(f"LLM流式API调用失败: {e.response.status_code if e.response else 'N/A'}, URL: {url}, Model: {model}, 错误详情: {error_detail}")
                # 发送错误信息
                yield f"data: {json.dumps({'error': error_detail}, ensure_ascii=False)}\n\n"
                raise
