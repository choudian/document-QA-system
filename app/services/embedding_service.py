"""
Embedding服务 - 基于LangChain实现
"""
from typing import List, Dict, Any, Optional
import json
import base64
import logging
from langchain_openai import OpenAIEmbeddings
from app.services.config_service import ConfigService
from app.repositories.config_repository import ConfigRepository

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Embedding服务 - 基于LangChain"""
    
    def __init__(self, config_service: ConfigService, config_repo: Optional[ConfigRepository] = None):
        self.config_service = config_service
        self.config_repo = config_repo
    
    def get_embedding_config(self, tenant_id: Optional[str]) -> Dict[str, Any]:
        """
        获取embedding配置（系统/租户级），包含未脱敏的API key
        
        Args:
            tenant_id: 租户ID
            
        Returns:
            embedding配置字典（包含真实的API key）
        """
        # 如果有config_repo，直接获取未脱敏的配置
        if self.config_repo:
            # 先尝试获取租户级配置
            if tenant_id:
                configs = self.config_repo.list_system_configs(tenant_id)
                for cfg in configs:
                    if cfg.category == "embedding" and cfg.key == "default":
                        value = json.loads(cfg.value)
                        # 解密敏感字段
                        if "api_key" in value and isinstance(value["api_key"], str):
                            value["api_key"] = self._decrypt(value["api_key"])
                        return value
            
            # 使用系统默认配置
            configs = self.config_repo.list_system_configs(None)
            for cfg in configs:
                if cfg.category == "embedding" and cfg.key == "default":
                    value = json.loads(cfg.value)
                    # 解密敏感字段
                    if "api_key" in value and isinstance(value["api_key"], str):
                        value["api_key"] = self._decrypt(value["api_key"])
                    return value
        
        # 如果没有config_repo，使用config_service（可能包含脱敏值）
        if tenant_id:
            configs = self.config_service.list_scope_configs("tenant", tenant_id)
            embedding_config = configs.get("embedding", {}).get("default")
            if embedding_config:
                return embedding_config
        
        configs = self.config_service.list_scope_configs("system", None)
        embedding_config = configs.get("embedding", {}).get("default")
        
        if not embedding_config:
            raise ValueError("未找到embedding配置")
        
        return embedding_config
    
    def _decrypt(self, text: str) -> str:
        """解密配置值"""
        if text.startswith("ENC:"):
            try:
                return base64.b64decode(text[4:].encode("utf-8")).decode("utf-8")
            except Exception:
                return text
        return text
    
    def _create_embeddings(self, config: Dict[str, Any]) -> OpenAIEmbeddings:
        """创建OpenAIEmbeddings实例"""
        base_url = config.get("base_url", "https://api.openai.com/v1")
        api_key = config.get("api_key", "")
        model = config.get("model", "text-embedding-3-small")
        
        # 解密API key
        if api_key.startswith("ENC:"):
            api_key = self._decrypt(api_key)
        
        # LangChain OpenAIEmbeddings支持自定义base_url和api_key
        # 注意：LangChain使用openai_api_key和openai_api_base参数
        # 使用 OpenAI API 格式，兼容所有支持 OpenAI API 的提供商
        return OpenAIEmbeddings(
            model=model,
            openai_api_key=api_key,
            openai_api_base=base_url,
            check_embedding_ctx_length=False,  # 禁用默认分词处理，兼容更多提供商
        )
    
    async def embed_text(self, text: str, tenant_id: Optional[str] = None) -> List[float]:
        """
        对单个文本进行embedding
        
        Args:
            text: 要embedding的文本
            tenant_id: 租户ID
            
        Returns:
            向量列表
        """
        # 验证输入参数
        if text is None:
            raise ValueError("text参数不能为None")
        if not isinstance(text, str):
            raise ValueError(f"text参数必须是字符串类型，当前类型: {type(text)}")
        if not text.strip():
            raise ValueError("text参数不能为空字符串")
        
        config = self.get_embedding_config(tenant_id)
        embeddings = self._create_embeddings(config)
        
        try:
            # LangChain的embed_query是同步的，需要在线程池中运行
            import asyncio
            loop = asyncio.get_event_loop()
            # 确保text是字符串类型
            text_str = str(text).strip()
            if not text_str:
                raise ValueError("text参数不能为空")
            vector = await loop.run_in_executor(None, embeddings.embed_query, text_str)
            return vector
        except Exception as e:
            logger.error(f"Embedding调用失败: text={repr(text)}, type={type(text)}, error={e}", exc_info=True)
            raise
    
    async def embed_batch(self, texts: List[str], tenant_id: Optional[str] = None) -> List[List[float]]:
        """
        批量embedding（优化性能）
        
        Args:
            texts: 要embedding的文本列表
            tenant_id: 租户ID
            
        Returns:
            向量列表的列表
        """
        if not texts:
            return []
        
        config = self.get_embedding_config(tenant_id)
        provider = config.get("provider", "openai")
        embeddings = self._create_embeddings(config)
        
        # 阿里云限制批量大小不能超过10
        batch_size = 10 if provider == "aliyun" else 2048  # OpenAI支持更大的批量
        
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            
            # 如果文本数量超过批量大小，需要分批处理
            if len(texts) <= batch_size:
                vectors = await loop.run_in_executor(None, embeddings.embed_documents, texts)
                return vectors
            else:
                # 分批处理
                all_vectors = []
                for i in range(0, len(texts), batch_size):
                    batch_texts = texts[i:i + batch_size]
                    logger.debug(f"分批embedding: {i+1}-{min(i+batch_size, len(texts))}/{len(texts)}")
                    batch_vectors = await loop.run_in_executor(None, embeddings.embed_documents, batch_texts)
                    all_vectors.extend(batch_vectors)
                return all_vectors
        except Exception as e:
            logger.error(f"批量Embedding调用失败: {e}", exc_info=True)
            raise
