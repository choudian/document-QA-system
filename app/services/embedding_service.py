"""
Embedding服务
"""
from typing import List, Dict, Any, Optional
import httpx
from app.services.config_service import ConfigService
from app.repositories.config_repository import ConfigRepository
import json
import base64
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Embedding服务"""
    
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
                        import json
                        value = json.loads(cfg.value)
                        # 解密敏感字段
                        if "api_key" in value and isinstance(value["api_key"], str):
                            value["api_key"] = self._decrypt(value["api_key"])
                        return value
            
            # 使用系统默认配置
            configs = self.config_repo.list_system_configs(None)
            for cfg in configs:
                if cfg.category == "embedding" and cfg.key == "default":
                    import json
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
    
    async def embed_text(self, text: str, tenant_id: Optional[str] = None) -> List[float]:
        """
        对单个文本进行embedding
        
        Args:
            text: 要embedding的文本
            tenant_id: 租户ID
            
        Returns:
            向量列表
        """
        config = self.get_embedding_config(tenant_id)
        return await self._embed_with_config(text, config)
    
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
        
        if provider == "openai" or provider == "aliyun":
            # 阿里云使用OpenAI兼容接口
            return await self._embed_batch_openai(texts, config)
        else:
            # 其他provider暂时逐个调用
            results = []
            for text in texts:
                vector = await self._embed_with_config(text, config)
                results.append(vector)
            return results
    
    async def _embed_with_config(self, text: str, config: Dict[str, Any]) -> List[float]:
        """使用配置进行embedding"""
        provider = config.get("provider", "openai")
        
        if provider == "openai" or provider == "aliyun":
            # 阿里云使用OpenAI兼容接口
            return await self._embed_openai(text, config)
        else:
            raise ValueError(f"不支持的embedding provider: {provider}")
    
    async def _embed_openai(self, text: str, config: Dict[str, Any]) -> List[float]:
        """使用OpenAI API进行embedding（也支持阿里云等兼容OpenAI接口的服务）"""
        base_url = config.get("base_url", "https://api.openai.com/v1")
        api_key = config.get("api_key", "")
        model = config.get("model", "text-embedding-3-small")
        
        # API key应该已经在get_embedding_config中解密了
        # 这里只需要处理ENC:前缀的情况（以防万一）
        if api_key.startswith("ENC:"):
            try:
                api_key = base64.b64decode(api_key[4:].encode("utf-8")).decode("utf-8")
            except Exception:
                pass
        
        url = f"{base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "input": text,
            "model": model
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            return result["data"][0]["embedding"]
    
    async def _embed_batch_openai(self, texts: List[str], config: Dict[str, Any]) -> List[List[float]]:
        """使用OpenAI API批量embedding（也支持阿里云等兼容OpenAI接口的服务）"""
        base_url = config.get("base_url", "https://api.openai.com/v1")
        api_key = config.get("api_key", "")
        model = config.get("model", "text-embedding-3-small")
        provider = config.get("provider", "openai")
        
        # API key应该已经在get_embedding_config中解密了
        if api_key.startswith("ENC:"):
            try:
                api_key = base64.b64decode(api_key[4:].encode("utf-8")).decode("utf-8")
            except Exception:
                pass
        
        # 阿里云限制批量大小不能超过10
        batch_size = 10 if provider == "aliyun" else 2048  # OpenAI支持更大的批量
        
        # 如果文本数量超过批量大小，需要分批处理
        if len(texts) <= batch_size:
            return await self._embed_batch_single(texts, base_url, api_key, model)
        else:
            # 分批处理
            all_vectors = []
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                logger.debug(f"分批embedding: {i+1}-{min(i+batch_size, len(texts))}/{len(texts)}")
                batch_vectors = await self._embed_batch_single(batch_texts, base_url, api_key, model)
                all_vectors.extend(batch_vectors)
            return all_vectors
    
    async def _embed_batch_single(self, texts: List[str], base_url: str, api_key: str, model: str) -> List[List[float]]:
        """执行单次批量embedding请求"""
        url = f"{base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "input": texts,
            "model": model
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                logger.debug(f"调用embedding API: {url}, model: {model}, texts数量: {len(texts)}")
                response = await client.post(url, headers=headers, json=data)
                response.raise_for_status()
                result = response.json()
                return [item["embedding"] for item in result["data"]]
            except httpx.HTTPStatusError as e:
                # 记录详细的错误信息
                error_detail = ""
                if e.response is not None:
                    try:
                        error_detail = e.response.json()
                    except:
                        error_detail = e.response.text[:500]  # 限制长度
                logger.error(f"Embedding API调用失败: {e.response.status_code if e.response else 'N/A'}, URL: {url}, Model: {model}, 错误详情: {error_detail}")
                raise

