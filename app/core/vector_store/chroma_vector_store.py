"""
Chroma向量库实现
"""
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.vector_store.vector_store_interface import VectorStoreInterface
from app.core.config import settings
from app.services.config_service import ConfigService
import os


class ChromaVectorStore(VectorStoreInterface):
    """Chroma向量库实现"""
    
    def __init__(self, config_service: ConfigService):
        self.config_service = config_service
        self.base_path = settings.VECTOR_STORE_BASE_PATH
        
        # 确保目录存在
        os.makedirs(self.base_path, exist_ok=True)
        
        # 创建持久化客户端
        self.client = chromadb.PersistentClient(
            path=self.base_path,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
    
    def get_collection_name(
        self,
        tenant_id: str,
        user_id: str,
        folder_id: Optional[str] = None
    ) -> str:
        """获取collection名称"""
        # 获取collection前缀
        vector_store_config = self._get_vector_store_config(tenant_id)
        prefix = vector_store_config.get("collection_prefix", "doc_qa")
        
        # folder_id为空时使用"root"
        folder_part = folder_id if folder_id else "root"
        
        # 命名格式：{prefix}_{tenant_id}_{user_id}_{folder_id}
        collection_name = f"{prefix}_{tenant_id}_{user_id}_{folder_part}"
        
        # Chroma collection名称限制：只能包含字母、数字、下划线和连字符
        # 替换UUID中的连字符为下划线
        collection_name = collection_name.replace("-", "_")
        
        return collection_name
    
    def _get_collection(
        self,
        tenant_id: str,
        user_id: str,
        folder_id: Optional[str] = None
    ):
        """获取或创建collection"""
        collection_name = self.get_collection_name(tenant_id, user_id, folder_id)
        
        try:
            collection = self.client.get_collection(name=collection_name)
        except Exception:
            # Collection不存在，创建新的
            collection = self.client.create_collection(
                name=collection_name,
                metadata={"tenant_id": tenant_id, "user_id": user_id, "folder_id": folder_id or "root"}
            )
        
        return collection
    
    def _get_vector_store_config(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """获取向量库配置（系统/租户级）"""
        # 先尝试获取租户级配置
        if tenant_id:
            configs = self.config_service.list_scope_configs("tenant", tenant_id)
            vector_store_config = configs.get("vector_store", {}).get("default")
            if vector_store_config:
                return vector_store_config
        
        # 使用系统级配置
        configs = self.config_service.list_scope_configs("system", None)
        vector_store_config = configs.get("vector_store", {}).get("default")
        
        if not vector_store_config:
            # 使用默认配置
            return {
                "provider": "chroma",
                "base_url": "",
                "api_key": "",
                "collection_prefix": "doc_qa"
            }
        
        return vector_store_config
    
    def add_vectors(
        self,
        vectors: List[List[float]],
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
        tenant_id: str,
        user_id: str,
        folder_id: Optional[str] = None
    ) -> bool:
        """添加向量到向量库"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            collection = self._get_collection(tenant_id, user_id, folder_id)
            collection_name = self.get_collection_name(tenant_id, user_id, folder_id)
            logger.info(f"准备添加 {len(vectors)} 个向量到 collection: {collection_name}")
            
            # 添加向量
            collection.add(
                embeddings=vectors,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"成功添加 {len(vectors)} 个向量到 collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"添加向量失败: {e}", exc_info=True)
            return False
    
    def search(
        self,
        query_vector: List[float],
        top_k: int,
        tenant_id: str,
        user_id: str,
        folder_id: Optional[str] = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """搜索相似向量"""
        try:
            collection = self._get_collection(tenant_id, user_id, folder_id)
            
            # 构建where条件
            where = None
            if filter_metadata:
                where = filter_metadata
            
            # 搜索
            results = collection.query(
                query_embeddings=[query_vector],
                n_results=top_k,
                where=where
            )
            
            # 格式化结果
            formatted_results = []
            if results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    formatted_results.append({
                        "id": results["ids"][0][i],
                        "text": results["documents"][0][i] if results["documents"] else None,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else None
                    })
            
            return formatted_results
        except Exception as e:
            print(f"搜索向量失败: {e}")
            return []
    
    def delete_by_document_id(
        self,
        document_id: str,
        tenant_id: str,
        user_id: str,
        folder_id: Optional[str] = None
    ) -> bool:
        """根据文档ID删除向量"""
        try:
            collection = self._get_collection(tenant_id, user_id, folder_id)
            
            # 查询包含该document_id的所有向量
            results = collection.get(
                where={"document_id": document_id}
            )
            
            if results["ids"]:
                # 删除这些向量
                collection.delete(ids=results["ids"])
            
            return True
        except Exception as e:
            print(f"删除向量失败: {e}")
            return False

