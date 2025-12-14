"""
Reranker服务 - 调用远端Reranker API
注意：由于阿里云DashScope的Reranker API格式特殊，这里使用httpx直接调用
但保持了与LangChain类似的抽象接口风格，支持配置分层和自定义base_url
"""
import logging
import json
import base64
from typing import List, Dict, Any, Optional
import httpx
from app.services.config_service import ConfigService
from app.repositories.config_repository import ConfigRepository

logger = logging.getLogger(__name__)


class RerankerService:
    """Reranker服务"""
    
    def __init__(self, config_service: ConfigService, config_repo: Optional[ConfigRepository] = None):
        self.config_service = config_service
        self.config_repo = config_repo
    
    def get_rerank_config(self, tenant_id: Optional[str], user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取Rerank配置（系统/租户/用户级），包含未脱敏的API key
        
        Args:
            tenant_id: 租户ID
            user_id: 用户ID（可选，用于获取用户级配置）
            
        Returns:
            Rerank配置字典（包含真实的API key）
        """
        # 如果有config_repo，直接获取未脱敏的配置
        if self.config_repo:
            # 先尝试获取用户级配置
            if user_id:
                configs = self.config_repo.list_user_configs(user_id)
                for cfg in configs:
                    if cfg.category == "rerank" and cfg.key == "default":
                        value = json.loads(cfg.value)
                        # 解密敏感字段
                        if "api_key" in value and isinstance(value["api_key"], str):
                            value["api_key"] = self._decrypt(value["api_key"])
                        return value
            
            # 尝试获取租户级配置
            if tenant_id:
                configs = self.config_repo.list_system_configs(tenant_id)
                for cfg in configs:
                    if cfg.category == "rerank" and cfg.key == "default":
                        value = json.loads(cfg.value)
                        # 解密敏感字段
                        if "api_key" in value and isinstance(value["api_key"], str):
                            value["api_key"] = self._decrypt(value["api_key"])
                        return value
            
            # 使用系统默认配置
            configs = self.config_repo.list_system_configs(None)
            for cfg in configs:
                if cfg.category == "rerank" and cfg.key == "default":
                    value = json.loads(cfg.value)
                    # 解密敏感字段
                    if "api_key" in value and isinstance(value["api_key"], str):
                        value["api_key"] = self._decrypt(value["api_key"])
                    return value
        
        # 如果没有config_repo，使用config_service（可能包含脱敏值）
        effective_config = self.config_service.get_effective_config(tenant_id, user_id)
        rerank_config = effective_config.get("rerank", {}).get("default")
        
        if not rerank_config:
            raise ValueError("未找到Rerank配置")
        
        return rerank_config
    
    def _decrypt(self, text: str) -> str:
        """解密配置值"""
        if text.startswith("ENC:"):
            try:
                return base64.b64decode(text[4:].encode("utf-8")).decode("utf-8")
            except Exception:
                return text
        return text
    
    async def rerank(
        self,
        query: str,
        documents: List[str],
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        top_n: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        对文档进行重排序
        
        Args:
            query: 查询文本
            documents: 待排序的文档列表
            tenant_id: 租户ID
            user_id: 用户ID
            top_n: 返回top N个结果（如果为None，返回所有结果）
        
        Returns:
            重排序后的结果列表，每个结果包含：
            - index: 原始索引
            - document: 文档内容
            - relevance_score: 相关性分数
        """
        if not documents:
            return []
        
        config = self.get_rerank_config(tenant_id, user_id)
        provider = config.get("provider", "aliyun")
        base_url = config.get("base_url", "https://dashscope.aliyuncs.com/api/v1/services/rerank/text-rerank/text-rerank")
        api_key = config.get("api_key", "")
        model = config.get("model", "qwen3-rerank")
        timeout = config.get("timeout", 30)
        
        # 解密API key
        if api_key.startswith("ENC:"):
            api_key = self._decrypt(api_key)
        
        # 构建请求数据
        request_data = {
            "model": model,
            "input": {
                "query": query,
                "documents": documents
            },
            "parameters": {
                "return_documents": True,
                "top_n": top_n if top_n is not None else len(documents)
            }
        }
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(base_url, headers=headers, json=request_data)
                response.raise_for_status()
                result = response.json()
                
                # 解析响应
                # 阿里云DashScope返回格式：
                # {
                #   "request_id": "...",
                #   "output": {
                #     "results": [
                #       {
                #         "index": 0,
                #         "document": {...},
                #         "relevance_score": 0.95
                #       }
                #     ]
                #   }
                # }
                
                output = result.get("output", {})
                results = output.get("results", [])
                
                # 转换为标准格式
                # 阿里云API返回的document字段，当return_documents=true时，应该是原始文档内容（字符串）
                reranked_results = []
                for item in results:
                    document_text = item.get("document", "")
                    # 如果document是对象，尝试提取text字段
                    if isinstance(document_text, dict):
                        document_text = document_text.get("text", "")
                    
                    reranked_results.append({
                        "index": item.get("index", 0),
                        "document": document_text,
                        "relevance_score": item.get("relevance_score", 0.0)
                    })
                
                # 按相关性分数降序排序（API已经排序，这里确保一下）
                reranked_results.sort(key=lambda x: x["relevance_score"], reverse=True)
                
                return reranked_results
        except httpx.HTTPStatusError as e:
            error_detail = ""
            if e.response is not None:
                try:
                    error_detail = e.response.json()
                except:
                    error_detail = e.response.text[:500]
            logger.error(f"Reranker API调用失败: {e.response.status_code if e.response else 'N/A'}, URL: {base_url}, Model: {model}, 错误详情: {error_detail}")
            raise
        except Exception as e:
            logger.error(f"Reranker调用异常: {e}", exc_info=True)
            raise
