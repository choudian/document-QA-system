"""
向量化服务
"""
from typing import Optional
import uuid
from app.models.document import Document
from app.models.document_config import DocumentConfig
from app.services.text_splitter_service import TextSplitterService
from app.services.embedding_service import EmbeddingService
from app.core.vector_store.vector_store_factory import VectorStoreFactory
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.core.storage.storage_factory import StorageFactory
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class VectorizationService:
    """向量化服务"""
    
    def __init__(
        self,
        text_splitter_service: TextSplitterService,
        embedding_service: EmbeddingService,
        chunk_repo: DocumentChunkRepository,
        config_service,
        config_repo=None
    ):
        self.text_splitter = text_splitter_service
        self.embedding_service = embedding_service
        self.chunk_repo = chunk_repo
        self.config_service = config_service
        self.config_repo = config_repo
    
    async def vectorize_document(
        self,
        document: Document,
        config: DocumentConfig,
        storage
    ) -> bool:
        """
        向量化文档
        
        Args:
            document: 文档对象
            config: 文档配置
            storage: 存储服务实例
            
        Returns:
            是否成功
        """
        try:
            # 1. 读取Markdown内容
            if not document.markdown_path:
                logger.error(f"文档 {document.id} 没有markdown_path")
                return False
            
            markdown_content = await storage.read_file(document.markdown_path)
            text = markdown_content.decode("utf-8")
            
            # 2. 获取文档的folder_id
            folder_id = document.folder_id
            
            # 3. 文本切分
            chunks = self.text_splitter.split_text(text, config)
            if not chunks:
                logger.warning(f"文档 {document.id} 切分后没有chunk")
                return False
            
            logger.info(f"文档 {document.id} 切分为 {len(chunks)} 个chunk")
            
            # 4. Embedding（批量）
            logger.info(f"文档 {document.id} 开始进行embedding，共 {len(chunks)} 个chunk")
            try:
                vectors = await self.embedding_service.embed_batch(chunks, document.tenant_id)
                logger.info(f"文档 {document.id} embedding完成，获得 {len(vectors)} 个向量")
            except Exception as e:
                logger.error(f"文档 {document.id} embedding失败: {e}", exc_info=True)
                return False
            
            if len(vectors) != len(chunks):
                logger.error(f"文档 {document.id} embedding数量不匹配: 期望 {len(chunks)}, 实际 {len(vectors)}")
                return False
            
            # 5. 创建向量库实例
            vector_store = VectorStoreFactory.create_from_config(
                document.tenant_id,
                self.config_service
            )
            
            # 6. 准备向量数据
            vector_ids = []
            metadatas = []
            for i, chunk in enumerate(chunks):
                vector_id = str(uuid.uuid4())
                vector_ids.append(vector_id)
                metadatas.append({
                    "document_id": document.id,
                    "chunk_index": i,
                    "tenant_id": document.tenant_id,
                    "user_id": document.user_id,
                    "folder_id": folder_id or "root"
                })
            
            # 7. 存储到向量库
            success = vector_store.add_vectors(
                vectors=vectors,
                texts=chunks,
                metadatas=metadatas,
                ids=vector_ids,
                tenant_id=document.tenant_id,
                user_id=document.user_id,
                folder_id=folder_id
            )
            
            if not success:
                logger.error(f"文档 {document.id} 向量存储失败")
                return False
            
            # 8. 保存chunk元数据到数据库
            from app.models.document_chunk import DocumentChunk
            chunk_objects = []
            for i, (chunk, vector_id) in enumerate(zip(chunks, vector_ids)):
                chunk_obj = DocumentChunk(
                    document_id=document.id,
                    folder_id=folder_id,
                    tenant_id=document.tenant_id,
                    user_id=document.user_id,
                    chunk_index=i,
                    content=chunk,
                    vector_id=vector_id,
                    chunk_metadata={"length": len(chunk)}
                )
                chunk_objects.append(chunk_obj)
            
            self.chunk_repo.create_batch(chunk_objects)
            self.chunk_repo.commit()
            
            logger.info(f"文档 {document.id} 向量化完成，共 {len(chunks)} 个chunk")
            return True
            
        except Exception as e:
            logger.error(f"文档 {document.id} 向量化失败: {e}", exc_info=True)
            self.chunk_repo.rollback()
            return False

