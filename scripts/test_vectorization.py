"""
手动测试向量化功能
"""
import sys
import os
import asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.document import Document
from app.repositories.document_repository import DocumentRepository
from app.repositories.document_config_repository import DocumentConfigRepository
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.repositories.config_repository import ConfigRepository
from app.services.document_service import DocumentService
from app.services.storage_service import StorageService
from app.services.document_parser_service import DocumentParserService
from app.services.config_service import ConfigService
from app.core.storage import get_storage
from sqlalchemy import desc

async def test_vectorization():
    db = SessionLocal()
    try:
        # 获取最新的文档
        doc_repo = DocumentRepository(db)
        latest_doc = db.query(Document).order_by(desc(Document.created_at)).first()
        
        if not latest_doc:
            print("没有找到文档")
            return
        
        print(f"测试文档: {latest_doc.id} - {latest_doc.name}")
        print(f"状态: {latest_doc.status}")
        print(f"markdown_path: {latest_doc.markdown_path}")
        
        # 检查配置
        config_repo = DocumentConfigRepository(db)
        config = config_repo.get_by_document_id(latest_doc.id)
        
        if not config:
            print("[ERROR] 文档配置不存在")
            return
        
        print(f"\n文档配置:")
        print(f"  chunk_size: {config.chunk_size}")
        print(f"  chunk_overlap: {config.chunk_overlap}")
        print(f"  split_method: {config.split_method}")
        
        # 创建服务
        storage_service = StorageService()
        parser_service = DocumentParserService()
        config_service = ConfigService(ConfigRepository(db))
        
        document_service = DocumentService(
            document_repo=doc_repo,
            document_version_repo=None,  # 暂时不需要
            document_config_repo=config_repo,
            folder_repo=None,  # 暂时不需要
            storage_service=storage_service,
            parser_service=parser_service,
            config_service=config_service
        )
        
        # 获取存储实例
        storage = get_storage()
        
        print("\n开始向量化...")
        try:
            await document_service._vectorize_document(latest_doc, storage)
            print("[SUCCESS] 向量化完成")
            
            # 检查结果
            chunk_repo = DocumentChunkRepository(db)
            chunks = chunk_repo.get_by_document_id(latest_doc.id)
            print(f"生成的chunk数量: {len(chunks)}")
            
        except Exception as e:
            print(f"[ERROR] 向量化失败: {e}")
            import traceback
            traceback.print_exc()
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_vectorization())

