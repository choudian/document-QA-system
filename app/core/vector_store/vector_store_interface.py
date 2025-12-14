"""
向量库接口
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class VectorStoreInterface(ABC):
    """向量库抽象接口"""
    
    @abstractmethod
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
        """
        添加向量到向量库
        
        Args:
            vectors: 向量列表
            texts: 文本列表
            metadatas: 元数据列表
            ids: 向量ID列表
            tenant_id: 租户ID
            user_id: 用户ID
            folder_id: 文件夹ID（可为空）
            
        Returns:
            是否成功
        """
        pass
    
    @abstractmethod
    def search(
        self,
        query_vector: List[float],
        top_k: int,
        tenant_id: str,
        user_id: str,
        folder_id: Optional[str] = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索相似向量
        
        Args:
            query_vector: 查询向量
            top_k: 返回前k个结果
            tenant_id: 租户ID
            user_id: 用户ID
            folder_id: 文件夹ID（可为空）
            filter_metadata: 元数据过滤条件
            
        Returns:
            搜索结果列表，每个结果包含：id, text, metadata, distance/score
        """
        pass
    
    @abstractmethod
    def delete_by_document_id(
        self,
        document_id: str,
        tenant_id: str,
        user_id: str,
        folder_id: Optional[str] = None
    ) -> bool:
        """
        根据文档ID删除向量
        
        Args:
            document_id: 文档ID
            tenant_id: 租户ID
            user_id: 用户ID
            folder_id: 文件夹ID（可为空）
            
        Returns:
            是否成功
        """
        pass
    
    @abstractmethod
    def get_collection_name(
        self,
        tenant_id: str,
        user_id: str,
        folder_id: Optional[str] = None
    ) -> str:
        """
        获取collection名称
        
        Args:
            tenant_id: 租户ID
            user_id: 用户ID
            folder_id: 文件夹ID（可为空）
            
        Returns:
            collection名称
        """
        pass

