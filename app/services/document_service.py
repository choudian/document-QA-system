"""
文档服务（应用服务层）
"""
import logging
from typing import Optional, Dict, Any, List
from fastapi import BackgroundTasks, HTTPException, status
from app.repositories.document_repository import DocumentRepository
from app.repositories.document_version_repository import DocumentVersionRepository
from app.repositories.document_config_repository import DocumentConfigRepository
from app.repositories.folder_repository import FolderRepository
from app.models.document import Document
from app.models.document_config import DocumentConfig
from app.services.storage_service import StorageService
from app.services.document_parser_service import DocumentParserService
from app.services.config_service import ConfigService
from app.services.document_domain_service import DocumentDomainService
from app.repositories.config_repository import ConfigRepository
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.core.exceptions import (
    DocumentNotFoundException,
    DocumentPermissionDeniedException,
    DocumentProcessingException,
    FolderNotFoundException,
    FolderPermissionDeniedException
)
from app.core.value_objects import DocumentQuery, DocumentStatus

logger = logging.getLogger(__name__)


class DocumentService:
    """文档应用服务层"""
    
    def __init__(
        self,
        document_repo: DocumentRepository,
        document_version_repo: DocumentVersionRepository,
        document_config_repo: DocumentConfigRepository,
        folder_repo: FolderRepository,
        storage_service: StorageService,
        parser_service: DocumentParserService,
        config_service: ConfigService
    ):
        self.document_repo = document_repo
        self.document_version_repo = document_version_repo
        self.document_config_repo = document_config_repo
        self.folder_repo = folder_repo
        self.storage_service = storage_service
        self.parser_service = parser_service
        self.config_service = config_service
        self.domain_service = DocumentDomainService(config_service)
    
    def _get_upload_config(self, tenant_id: str) -> Dict[str, Any]:
        """获取上传配置（系统/租户级）"""
        effective_config = self.config_service.get_effective_config(tenant_id, None)
        upload_config = effective_config.get("doc", {}).get("upload", {})
        
        # 如果没有配置，返回默认值
        if not upload_config:
            return {
                "upload_types": ["txt", "md", "pdf", "word"],
                "max_file_size_mb": 50
            }
        
        return upload_config
    
    def _get_chunk_config(self, tenant_id: str) -> Dict[str, Any]:
        """获取文本切分配置（系统/租户级）"""
        effective_config = self.config_service.get_effective_config(tenant_id, None)
        chunk_config = effective_config.get("doc", {}).get("chunk", {})
        
        # 如果没有配置，返回默认值
        if not chunk_config:
            return {
                "strategy": "fixed",
                "size": 400,
                "overlap": 100
            }
        
        return chunk_config
    
    def check_duplicate(
        self,
        filename: str,
        folder_id: Optional[str],
        tenant_id: str,
        user_id: str
    ) -> Optional[Document]:
        """检查同名文件"""
        return self.document_repo.check_duplicate(filename, folder_id, tenant_id, user_id)
    
    async def upload_document(
        self,
        file_content: bytes,
        filename: str,
        folder_id: Optional[str],
        tenant_id: str,
        user_id: str,
        config_data: Optional[Dict[str, Any]] = None,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> Document:
        """上传文档"""
        # 验证文件夹
        if folder_id:
            folder = self.folder_repo.get_by_id(folder_id, tenant_id)
            if not folder or folder.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="文件夹不存在或无权限"
                )
            folder_path = folder.path
        else:
            folder_path = ""
        
        # 获取上传配置
        upload_config = self._get_upload_config(tenant_id)
        allowed_types = upload_config.get("upload_types", ["txt", "md", "pdf", "word"])
        max_size_mb = upload_config.get("max_file_size_mb", 50)
        max_size_bytes = max_size_mb * 1024 * 1024
        
        # 验证文件大小
        if len(file_content) > max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"文件大小超过限制（最大 {max_size_mb}MB）"
            )
        
        # 验证文件类型
        file_ext = filename.split(".")[-1].lower() if "." in filename else ""
        type_map = {
            "txt": "txt",
            "md": "md",
            "markdown": "md",
            "pdf": "pdf",
            "doc": "word",
            "docx": "word"
        }
        file_type = type_map.get(file_ext)
        
        if not file_type or file_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件类型，允许的类型: {', '.join(allowed_types)}"
            )
        
        # 生成文件哈希
        file_hash = self.storage_service.generate_file_hash(file_content)
        
        # 检查是否存在同名文件（用于版本管理）
        existing_doc_by_name = self.document_repo.check_duplicate(filename, folder_id, tenant_id, user_id)
        
        # 检查是否已存在相同文件（用于存储路径复用）
        existing_doc_by_hash = self.document_repo.get_by_hash(file_hash, tenant_id)
        if existing_doc_by_hash and existing_doc_by_hash.user_id == user_id:
            # 可以复用存储路径
            storage_path = existing_doc_by_hash.storage_path
        else:
            # 保存文件（异步方式）
            storage_path = await self.storage_service.save_file(
                file_content,
                tenant_id,
                user_id,
                folder_path,
                filename
            )
        
        # 确定MIME类型
        mime_map = {
            "txt": "text/plain",
            "md": "text/markdown",
            "pdf": "application/pdf",
            "word": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        }
        mime_type = mime_map.get(file_type, "application/octet-stream")
        
        # 如果存在同名文件，创建新版本并保存旧版本到版本历史
        old_document_id = None
        if existing_doc_by_name:
            # 保存旧版本到版本历史表
            from app.models.document_version import DocumentVersion
            old_version = DocumentVersion(
                document_id=existing_doc_by_name.id,
                version=existing_doc_by_name.version,
                file_hash=existing_doc_by_name.file_hash,
                storage_path=existing_doc_by_name.storage_path,
                markdown_path=existing_doc_by_name.markdown_path,
                operator_id=user_id,
                is_current=False  # 旧版本不再是当前版本
            )
            self.document_version_repo.create(old_version)
            
            # 获取下一个版本号（基于旧文档的版本历史）
            next_version = self.document_version_repo.get_next_version_number(existing_doc_by_name.id)
            old_document_id = existing_doc_by_name.id
            
            # 创建新版本文档（使用新的ID，但记录旧版本ID用于后续清理）
            document = Document(
                tenant_id=tenant_id,
                user_id=user_id,
                folder_id=folder_id,
                name=filename,
                original_name=filename,
                file_type=file_type,
                mime_type=mime_type,
                file_size=len(file_content),
                file_hash=file_hash,
                storage_path=storage_path,
                version=next_version,
                status="uploaded"
            )
            document = self.document_repo.create(document)
            
            # 创建新版本的版本历史记录（标记为当前版本）
            new_version = DocumentVersion(
                document_id=document.id,
                version=document.version,
                file_hash=document.file_hash,
                storage_path=document.storage_path,
                operator_id=user_id,
                is_current=True
            )
            self.document_version_repo.create(new_version)
        else:
            # 创建新文档（无同名文件，首次上传）
            document = Document(
                tenant_id=tenant_id,
                user_id=user_id,
                folder_id=folder_id,
                name=filename,
                original_name=filename,
                file_type=file_type,
                mime_type=mime_type,
                file_size=len(file_content),
                file_hash=file_hash,
                storage_path=storage_path,
                status="uploaded"
            )
            document = self.document_repo.create(document)
        
        # 保存文档配置
        chunk_config = self._get_chunk_config(tenant_id)
        if config_data:
            # 使用用户提供的配置
            doc_config = DocumentConfig(
                document_id=document.id,
                chunk_size=config_data.get("chunk_size", chunk_config.get("size", 400)),
                chunk_overlap=config_data.get("chunk_overlap", chunk_config.get("overlap", 100)),
                split_method=config_data.get("split_method", chunk_config.get("strategy", "fixed")),
                split_keyword=config_data.get("split_keyword")
            )
        else:
            # 使用租户默认配置
            doc_config = DocumentConfig(
                document_id=document.id,
                chunk_size=chunk_config.get("size", 400),
                chunk_overlap=chunk_config.get("overlap", 100),
                split_method=chunk_config.get("strategy", "fixed")
            )
        
        self.document_config_repo.create(doc_config)
        
        # 更新用户最近配置
        if config_data:
            self.document_config_repo.create_or_update_user_recent_config(
                user_id,
                chunk_size=doc_config.chunk_size,
                chunk_overlap=doc_config.chunk_overlap,
                split_method=doc_config.split_method,
                split_keyword=doc_config.split_keyword
            )
        
        # 异步解析文档（使用后台任务）
        # 传递旧文档ID，用于新版本向量化成功后清理旧版本向量数据
        if background_tasks:
            background_tasks.add_task(
                self._parse_document_async,
                document.id,
                storage_path,
                file_type,
                old_document_id  # 传递旧文档ID
            )
        
        return document
    
    async def _parse_document_async(self, document_id: str, storage_path: str, file_type: str, old_document_id: Optional[str] = None):
        """异步解析文档
        
        Args:
            document_id: 新文档ID
            storage_path: 存储路径
            file_type: 文件类型
            old_document_id: 旧文档ID（如果存在，用于新版本向量化成功后清理旧版本向量数据）
        """
        try:
            document = self.document_repo.get_by_id(document_id)
            if not document:
                logger.error(f"文档不存在: {document_id}")
                return
            
            # 更新状态为解析中
            document.mark_as_parsing()
            self.document_repo.update(document)
            
            # 解析文档
            from app.core.storage import get_storage
            storage = get_storage()
            
            result = await self.parser_service.parse_document_with_retry(
                storage_path,
                file_type,
                storage,
                max_retries=3
            )
            
            if result:
                # 保存Markdown结果（异步方式）
                markdown_content = result["content"].encode("utf-8")
                # 生成markdown路径（替换文件扩展名）
                if "." in storage_path:
                    markdown_path = ".".join(storage_path.split(".")[:-1]) + ".md"
                else:
                    markdown_path = f"{storage_path}.md"
                await storage.save_file(markdown_path, markdown_content)
                
                # 更新文档
                document.update_parsing_result(
                    markdown_path=markdown_path,
                    title=result.get("title"),
                    summary=result.get("summary"),
                    page_count=result.get("metadata", {}).get("page_count")
                )
                self.document_repo.update(document)
                
                # 向量化文档
                try:
                    success = await self._vectorize_document(document, storage)
                    # 如果向量化成功且存在旧版本，清理旧版本的向量数据
                    if success and old_document_id:
                        await self._cleanup_old_version_vectors(old_document_id, document.tenant_id, document.user_id, document.folder_id)
                except Exception as e:
                    logger.error(f"文档 {document_id} 向量化失败: {e}", exc_info=True)
                    # 向量化失败不影响文档解析成功状态
            else:
                # 解析失败
                document.mark_as_parse_failed()
                # 注意：待办表功能为预留接口，暂不实现自动加入待办表的逻辑
                self.document_repo.update(document)
            
        except Exception as e:
            logger.error(f"解析文档失败: {document_id}, 错误: {e}", exc_info=True)
            document = self.document_repo.get_by_id(document_id)
            if document:
                document.mark_as_parse_failed()
                self.document_repo.update(document)
    
    async def _vectorize_document(self, document: Document, storage):
        """向量化文档"""
        # 获取文档配置
        config = self.document_config_repo.get_by_document_id(document.id)
        if not config:
            logger.warning(f"文档 {document.id} 没有配置，跳过向量化")
            return False
        
        # 创建向量化服务所需的依赖
        from app.services.text_splitter_service import TextSplitterService
        from app.services.embedding_service import EmbeddingService
        from app.services.vectorization_service import VectorizationService
        
        # 使用document_repo的db会话
        db = self.document_repo.db
        
        from app.repositories.config_repository import ConfigRepository
        
        text_splitter = TextSplitterService()
        config_repo = ConfigRepository(db)
        embedding_service = EmbeddingService(self.config_service, config_repo)
        chunk_repo = DocumentChunkRepository(db)
        
        vectorization_service = VectorizationService(
            text_splitter_service=text_splitter,
            embedding_service=embedding_service,
            chunk_repo=chunk_repo,
            config_service=self.config_service,
            config_repo=config_repo
        )
        
        # 更新文档状态为向量化中
        document.status = "vectorizing"
        self.document_repo.update(document)
        
        # 执行向量化
        success = await vectorization_service.vectorize_document(
            document=document,
            config=config,
            storage=storage
        )
        
        if success:
            logger.info(f"文档 {document.id} 向量化成功")
            # 标记文档为已完成
            document.mark_as_completed()
            self.document_repo.update(document)
        else:
            logger.warning(f"文档 {document.id} 向量化失败")
            document.mark_as_vectorize_failed()
            self.document_repo.update(document)
        return success
    
    async def _cleanup_old_version_vectors(
        self,
        old_document_id: str,
        tenant_id: str,
        user_id: str,
        folder_id: Optional[str]
    ):
        """清理旧版本的向量数据
        
        Args:
            old_document_id: 旧文档ID
            tenant_id: 租户ID
            user_id: 用户ID
            folder_id: 文件夹ID
        """
        try:
            logger.info(f"开始清理旧版本文档 {old_document_id} 的向量数据")
            
            # 获取旧文档信息
            old_document = self.document_repo.get_by_id(old_document_id, tenant_id)
            if not old_document:
                logger.warning(f"旧文档 {old_document_id} 不存在，跳过清理")
                return
            
            # 删除向量库索引
            try:
                from app.core.vector_store.vector_store_factory import VectorStoreFactory
                
                vector_store = VectorStoreFactory.create_from_config(
                    tenant_id,
                    self.config_service
                )
                vector_store.delete_by_document_id(
                    document_id=old_document_id,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    folder_id=folder_id
                )
                logger.info(f"已删除旧文档 {old_document_id} 的向量库索引")
            except Exception as e:
                logger.error(f"删除旧文档 {old_document_id} 的向量库索引失败: {e}", exc_info=True)
            
            # 删除文档chunk数据
            try:
                chunk_repo = DocumentChunkRepository(self.document_repo.db)
                deleted_count = chunk_repo.delete_by_document_id(old_document_id)
                logger.info(f"已删除旧文档 {old_document_id} 的 {deleted_count} 个chunk")
            except Exception as e:
                logger.error(f"删除旧文档 {old_document_id} 的chunk失败: {e}", exc_info=True)
            
            logger.info(f"完成清理旧版本文档 {old_document_id} 的向量数据")
        except Exception as e:
            logger.error(f"清理旧版本文档 {old_document_id} 的向量数据失败: {e}", exc_info=True)
    
    def list_documents(
        self,
        user_id: str,
        tenant_id: str,
        folder_id: Optional[str] = None,
        status: Optional[str] = None,
        tag: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Document]:
        """查询文档列表"""
        query = DocumentQuery(
            tenant_id=tenant_id,
            user_id=user_id,
            folder_id=folder_id,
            status=status,
            tag=tag,
            skip=skip,
            limit=limit
        )
        query.validate()
        
        # 如果指定了标签，使用标签搜索
        if tag:
            return self._list_documents_by_tag(query)
        else:
            # 普通查询
            return self.document_repo.list_by_user(
                user_id, tenant_id, folder_id, status, skip, limit
            )
    
    def _list_documents_by_tag(self, query: DocumentQuery) -> List[Document]:
        """按标签查询文档列表"""
        from app.repositories.document_tag_repository import DocumentTagRepository
        tag_repo = DocumentTagRepository(self.document_repo.db)
        document_ids = tag_repo.search_documents_by_tag(query.tag, query.user_id, query.tenant_id)
        
        # 提取ID列表（处理可能的元组或字符串格式）
        doc_id_list = []
        for doc_id in document_ids:
            if isinstance(doc_id, tuple):
                doc_id_list.append(doc_id[0])
            elif isinstance(doc_id, str):
                doc_id_list.append(doc_id)
            else:
                # 如果是SQLAlchemy的Row对象，尝试获取第一个元素
                try:
                    doc_id_list.append(doc_id[0])
                except (TypeError, IndexError):
                    doc_id_list.append(str(doc_id))
        
        if not doc_id_list:
            return []
        
        # 根据ID列表查询文档
        documents = self.document_repo.db.query(Document).filter(
            Document.id.in_(doc_id_list),
            Document.tenant_id == query.tenant_id,
            Document.user_id == query.user_id,
            Document.deleted_at.is_(None)
        )
        if query.folder_id is not None:
            documents = documents.filter(Document.folder_id == query.folder_id)
        if query.status:
            documents = documents.filter(Document.status == query.status)
        return documents.order_by(Document.created_at.desc()).offset(query.skip).limit(query.limit).all()
    
    def get_document(self, document_id: str, tenant_id: str, user_id: str) -> Document:
        """获取文档详情"""
        document = self.document_repo.get_by_id(document_id, tenant_id)
        if not document:
            raise DocumentNotFoundException(document_id)
        
        # 验证权限
        if not document.is_owned_by(user_id):
            raise DocumentPermissionDeniedException(document_id)
        
        return document
    
    def delete_document(self, document_id: str, tenant_id: str, user_id: str) -> bool:
        """删除文档（软删除）"""
        document = self.get_document(document_id, tenant_id, user_id)
        
        # 等待处理完成
        if not document.can_be_deleted():
            raise DocumentProcessingException(document_id, document.status)
        
        # 删除向量库索引
        try:
            from app.core.vector_store.vector_store_factory import VectorStoreFactory
            from app.repositories.config_repository import ConfigRepository
            
            config_repo = ConfigRepository(self.document_repo.db)
            vector_store = VectorStoreFactory.create_from_config(
                tenant_id,
                self.config_service,
                config_repo
            )
            vector_store.delete_by_document_id(
                document_id=document_id,
                tenant_id=tenant_id,
                user_id=user_id,
                folder_id=document.folder_id
            )
            logger.info(f"已删除文档 {document_id} 的向量库索引")
        except Exception as e:
            logger.error(f"删除文档 {document_id} 的向量库索引失败: {e}", exc_info=True)
            # 向量库删除失败不影响文档删除
        
        # 删除文档chunk数据
        try:
            chunk_repo = DocumentChunkRepository(self.document_repo.db)
            deleted_count = chunk_repo.delete_by_document_id(document_id)
            logger.info(f"已删除文档 {document_id} 的 {deleted_count} 个chunk")
        except Exception as e:
            logger.error(f"删除文档 {document_id} 的chunk失败: {e}", exc_info=True)
            # chunk删除失败不影响文档删除
        
        # 删除文档配置
        try:
            self.document_config_repo.delete(document_id)
        except Exception as e:
            logger.warning(f"删除文档 {document_id} 的配置失败: {e}")
        
        # 软删除文档
        document.soft_delete()
        self.document_repo.update(document)
        return True
    
    def get_document_versions(self, document_id: str, tenant_id: str, user_id: str) -> List:
        """获取文档版本历史"""
        document = self.get_document(document_id, tenant_id, user_id)
        return self.document_version_repo.list_by_document(document.id)
    
    def restore_document(self, document_id: str, tenant_id: str, user_id: str) -> Document:
        """恢复软删除的文档"""
        # 查询已删除的文档（包括软删除的）
        document = self.document_repo.db.query(Document).filter(
            Document.id == document_id,
            Document.tenant_id == tenant_id,
            Document.user_id == user_id,
            Document.deleted_at.isnot(None)
        ).first()
        
        if not document:
            raise DocumentNotFoundException(document_id)
        
        # 恢复文档
        document.restore()
        self.document_repo.update(document)
        
        # 注意：恢复后如果向量数据已删除，需要重新向量化
        # 这里不自动触发向量化，由用户手动触发或系统后台任务处理
        
        logger.info(f"已恢复文档 {document_id}")
        return document
    
    def list_trash_documents(
        self,
        tenant_id: str,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Document]:
        """查询回收站文档列表"""
        return self.document_repo.db.query(Document).filter(
            Document.tenant_id == tenant_id,
            Document.user_id == user_id,
            Document.deleted_at.isnot(None)
        ).order_by(Document.deleted_at.desc()).offset(skip).limit(limit).all()

