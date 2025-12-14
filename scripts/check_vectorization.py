"""
检查向量化状态的调试脚本
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.document import Document
from app.models.document_config import DocumentConfig
from app.models.document_chunk import DocumentChunk
from sqlalchemy import desc

def main():
    db = SessionLocal()
    try:
        # 获取最新的文档
        latest_doc = db.query(Document).order_by(desc(Document.created_at)).first()
        
        if not latest_doc:
            print("没有找到文档")
            return
        
        print(f"最新文档: {latest_doc.id}")
        print(f"  名称: {latest_doc.name}")
        print(f"  状态: {latest_doc.status}")
        print(f"  markdown_path: {latest_doc.markdown_path}")
        print(f"  folder_id: {latest_doc.folder_id}")
        
        # 检查配置
        config = db.query(DocumentConfig).filter(
            DocumentConfig.document_id == latest_doc.id
        ).first()
        
        if config:
            print(f"\n文档配置存在:")
            print(f"  chunk_size: {config.chunk_size}")
            print(f"  chunk_overlap: {config.chunk_overlap}")
            print(f"  split_method: {config.split_method}")
        else:
            print("\n[WARNING] 文档配置不存在！这可能是向量化失败的原因。")
        
        # 检查chunk
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == latest_doc.id
        ).all()
        
        print(f"\nChunk数量: {len(chunks)}")
        if chunks:
            print("前3个chunk:")
            for i, chunk in enumerate(chunks[:3]):
                print(f"  Chunk {i}: index={chunk.chunk_index}, vector_id={chunk.vector_id}, content_length={len(chunk.content)}")
        else:
            print("[WARNING] 没有找到chunk，向量化可能未执行或失败")
        
        # 检查vector_store目录
        import os
        vector_store_path = "./vector_store"
        if os.path.exists(vector_store_path):
            print(f"\n[OK] vector_store目录存在: {os.path.abspath(vector_store_path)}")
            files = os.listdir(vector_store_path)
            print(f"  目录内容: {files[:10]}... (共{len(files)}项)")
        else:
            print(f"\n[WARNING] vector_store目录不存在: {os.path.abspath(vector_store_path)}")
            print("  向量化可能未执行或失败")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()

