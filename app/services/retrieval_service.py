"""
检索服务
"""
import logging
from typing import List, Dict, Any, Optional
from app.services.embedding_service import EmbeddingService
from app.services.config_service import ConfigService
from app.core.vector_store.vector_store_factory import VectorStoreFactory
from app.repositories.folder_repository import FolderRepository
from app.repositories.document_chunk_repository import DocumentChunkRepository

logger = logging.getLogger(__name__)


class RetrievalService:
    """检索服务"""
    
    def __init__(
        self,
        embedding_service: EmbeddingService,
        config_service: ConfigService,
        folder_repo: FolderRepository,
        chunk_repo: DocumentChunkRepository
    ):
        self.embedding_service = embedding_service
        self.config_service = config_service
        self.folder_repo = folder_repo
        self.chunk_repo = chunk_repo
    
    def _get_all_folder_ids(self, folder_id: str, tenant_id: str, user_id: str) -> List[str]:
        """获取文件夹及其所有子文件夹的ID列表"""
        folder_ids = [folder_id]
        
        # 递归获取所有子文件夹
        def get_children(parent_id: str):
            children = self.folder_repo.list_by_user(user_id, tenant_id, parent_id)
            for child in children:
                folder_ids.append(child.id)
                get_children(child.id)  # 递归获取子文件夹的子文件夹
        
        get_children(folder_id)
        return folder_ids
    
    async def search(
        self,
        query: str,
        tenant_id: str,
        user_id: str,
        knowledge_base_ids: Optional[List[str]] = None,  # 文件夹ID列表
        top_k: int = 5,
        similarity_threshold: Optional[float] = None,
        use_rerank: bool = False,
        rerank_top_n: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        检索相关内容
        
        Args:
            query: 查询文本
            tenant_id: 租户ID
            user_id: 用户ID
            knowledge_base_ids: 知识库（文件夹）ID列表，如果为None或空，则搜索用户的所有文件夹
            top_k: 返回top K个结果
            similarity_threshold: 相似度阈值（可选）
            use_rerank: 是否使用重排序
            rerank_top_n: 重排序后的top N（仅在use_rerank=True时使用）
        
        Returns:
            检索结果列表，每个结果包含：
            - document_id: 文档ID
            - chunk_index: chunk索引
            - content: chunk内容
            - similarity: 相似度分数
            - metadata: 元数据（包含文档名称、标题等）
        """
        # 1. 对查询文本进行embedding
        query_vector = await self.embedding_service.embed_text(query, tenant_id)
        
        # 2. 确定要搜索的文件夹列表
        if not knowledge_base_ids:
            # 如果没有指定知识库，搜索用户的所有文件夹
            all_folders = self.folder_repo.list_by_user(user_id, tenant_id, None)
            folder_ids = []
            # 递归获取所有文件夹（包括子文件夹）
            def get_all_folders(parent_id: Optional[str] = None):
                folders = self.folder_repo.list_by_user(user_id, tenant_id, parent_id)
                for folder in folders:
                    folder_ids.append(folder.id)
                    get_all_folders(folder.id)
            
            get_all_folders(None)
            # 还需要包含根目录（folder_id为None的文档）
            folder_ids_to_search = [None] + folder_ids
        else:
            # 如果指定了知识库，需要包含所有子文件夹
            folder_ids_to_search = []
            for folder_id in knowledge_base_ids:
                # 验证文件夹权限
                folder = self.folder_repo.get_by_id(folder_id, tenant_id)
                if not folder or folder.user_id != user_id:
                    logger.warning(f"文件夹 {folder_id} 不存在或无权限，跳过")
                    continue
                
                # 获取文件夹及其所有子文件夹
                all_folder_ids = self._get_all_folder_ids(folder_id, tenant_id, user_id)
                folder_ids_to_search.extend([fid for fid in all_folder_ids])
            
            # 去重
            folder_ids_to_search = list(set(folder_ids_to_search))
        
        # 3. 在每个文件夹中进行向量检索
        all_results = []
        vector_store = VectorStoreFactory.create_from_config(tenant_id, self.config_service)
        
        for folder_id in folder_ids_to_search:
            try:
                # 执行向量检索
                results = vector_store.search(
                    query_vector=query_vector,
                    top_k=top_k * 2,  # 多检索一些，后续可能需要重排序
                    tenant_id=tenant_id,
                    user_id=user_id,
                    folder_id=folder_id
                )
                
                # 格式化结果
                for result in results:
                    metadata = result.get("metadata", {})
                    document_id = metadata.get("document_id")
                    chunk_index = metadata.get("chunk_index")
                    
                    if not document_id or chunk_index is None:
                        continue
                    
                    # 计算相似度分数（distance越小，相似度越高）
                    distance = result.get("distance", 1.0)
                    similarity = 1.0 - distance  # 转换为相似度（0-1之间，越大越相似）
                    
                    # 如果设置了相似度阈值，过滤掉相似度太低的
                    if similarity_threshold and similarity < similarity_threshold:
                        continue
                    
                    # 获取chunk的详细信息
                    chunk = self.chunk_repo.get_by_document_and_index(document_id, chunk_index)
                    if not chunk:
                        continue
                    
                    all_results.append({
                        "document_id": document_id,
                        "chunk_index": chunk_index,
                        "content": result.get("text", chunk.content),
                        "similarity": similarity,
                        "distance": distance,
                        "vector_id": result.get("id"),
                        "metadata": {
                            **metadata,
                            "chunk_metadata": chunk.chunk_metadata
                        }
                    })
            except Exception as e:
                logger.error(f"在文件夹 {folder_id} 中检索失败: {e}", exc_info=True)
                continue
        
        # 4. 按相似度排序
        all_results.sort(key=lambda x: x["similarity"], reverse=True)
        
        # 5. 如果启用了重排序，进行重排序（目前先简化，后续可以实现）
        if use_rerank and rerank_top_n:
            # TODO: 实现重排序逻辑
            # 目前先取前rerank_top_n个
            all_results = all_results[:rerank_top_n]
        else:
            # 只取top_k个
            all_results = all_results[:top_k]
        
        # 6. 补充文档信息（如果需要的话，可以从document_repo获取）
        # 这里先返回基本信息，后续可以根据需要补充
        
        return all_results
