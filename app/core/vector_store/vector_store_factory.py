"""
向量库工厂
"""
from typing import Optional
from app.core.vector_store.vector_store_interface import VectorStoreInterface
from app.core.vector_store.chroma_vector_store import ChromaVectorStore
from app.services.config_service import ConfigService


class VectorStoreFactory:
    """向量库工厂类"""
    
    @staticmethod
    def create_vector_store(
        provider: str,
        config_service: ConfigService
    ) -> VectorStoreInterface:
        """
        根据provider创建向量库实例
        
        Args:
            provider: 向量库provider（chroma/pgvector/milvus等）
            config_service: 配置服务
            
        Returns:
            向量库实例
        """
        if provider == "chroma":
            return ChromaVectorStore(config_service)
        elif provider == "pgvector":
            # TODO: 实现PGVector
            raise NotImplementedError("PGVector暂未实现")
        elif provider == "milvus":
            # TODO: 实现Milvus
            raise NotImplementedError("Milvus暂未实现")
        else:
            raise ValueError(f"不支持的向量库provider: {provider}")
    
    @staticmethod
    def create_from_config(
        tenant_id: Optional[str],
        config_service: ConfigService
    ) -> VectorStoreInterface:
        """
        从配置创建向量库实例
        
        Args:
            tenant_id: 租户ID
            config_service: 配置服务
            
        Returns:
            向量库实例
        """
        # 获取向量库配置
        if tenant_id:
            configs = config_service.list_scope_configs("tenant", tenant_id)
            vector_store_config = configs.get("vector_store", {}).get("default")
            if vector_store_config:
                provider = vector_store_config.get("provider", "chroma")
                return VectorStoreFactory.create_vector_store(provider, config_service)
        
        # 使用系统默认配置
        configs = config_service.list_scope_configs("system", None)
        vector_store_config = configs.get("vector_store", {}).get("default")
        
        if not vector_store_config:
            # 默认使用Chroma
            return ChromaVectorStore(config_service)
        
        provider = vector_store_config.get("provider", "chroma")
        return VectorStoreFactory.create_vector_store(provider, config_service)

