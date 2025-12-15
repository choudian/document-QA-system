"""
检索服务测试
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.services.retrieval_service import RetrievalService
from app.services.embedding_service import EmbeddingService
from app.services.config_service import ConfigService

@pytest.mark.unit
@pytest.mark.asyncio
async def test_retrieval_service_search_empty_query():
    """测试空查询"""
    # Mock dependencies
    embedding_service = Mock(spec=EmbeddingService)
    config_service = Mock(spec=ConfigService)
    folder_repo = Mock()
    chunk_repo = Mock()
    document_repo = Mock()
    reranker_service = Mock()
    
    retrieval_service = RetrievalService(
        embedding_service=embedding_service,
        config_service=config_service,
        folder_repo=folder_repo,
        chunk_repo=chunk_repo,
        document_repo=document_repo,
        reranker_service=reranker_service
    )
    
    results = await retrieval_service.search(
        query="",
        tenant_id="test_tenant",
        user_id="test_user",
        knowledge_base_ids=[],
        top_k=5
    )
    
    assert results == []

@pytest.mark.unit
@pytest.mark.asyncio
async def test_retrieval_service_search_with_embedding():
    """测试带embedding的检索"""
    # Mock dependencies
    embedding_service = Mock(spec=EmbeddingService)
    embedding_service.embed_query = AsyncMock(return_value=[0.1] * 1536)
    
    config_service = Mock(spec=ConfigService)
    folder_repo = Mock()
    chunk_repo = Mock()
    document_repo = Mock()
    reranker_service = Mock()
    
    retrieval_service = RetrievalService(
        embedding_service=embedding_service,
        config_service=config_service,
        folder_repo=folder_repo,
        chunk_repo=chunk_repo,
        document_repo=document_repo,
        reranker_service=reranker_service
    )
    
    # Mock vector store search
    with patch('app.services.retrieval_service.VectorStoreFactory') as mock_factory:
        mock_vector_store = Mock()
        mock_vector_store.search = AsyncMock(return_value=[])
        mock_factory.create_from_config.return_value = mock_vector_store
        
        results = await retrieval_service.search(
            query="测试查询",
            tenant_id="test_tenant",
            user_id="test_user",
            knowledge_base_ids=[],
            top_k=5
        )
        
        assert isinstance(results, list)
        embedding_service.embed_query.assert_called_once()
