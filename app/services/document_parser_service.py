"""
文档解析服务
"""
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from app.core.parsers import ParserFactory, ParserInterface
from app.core.storage import StorageInterface

logger = logging.getLogger(__name__)


class DocumentParserService:
    """文档解析服务"""
    
    def __init__(self, storage: Optional[StorageInterface] = None):
        self.storage = storage
    
    async def parse_document(
        self,
        file_path: str,
        file_type: str,
        storage: StorageInterface
    ) -> Dict[str, Any]:
        """
        解析文档（异步）
        
        Args:
            file_path: 文件存储路径（相对路径）
            file_type: 文件类型（txt/md/pdf/word）
            storage: 存储接口实例
        
        Returns:
            解析结果，包含：
            - content: Markdown格式的内容
            - title: 文档标题
            - summary: 摘要
            - metadata: 元数据
        """
        try:
            # 获取解析器
            parser = ParserFactory.get_parser_by_type(file_type)
            
            # 读取文件内容（异步方式）
            file_content = await storage.read_file(file_path)
            
            # 创建临时文件用于解析
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type}") as tmp_file:
                tmp_file.write(file_content)
                tmp_path = tmp_file.name
            
            try:
                # 解析文件
                result = parser.parse(tmp_path)
                
                # 提取元数据
                metadata = parser.extract_metadata(tmp_path)
                result["metadata"].update(metadata)
                
                return result
            finally:
                # 清理临时文件
                try:
                    Path(tmp_path).unlink()
                except Exception:
                    pass  # 忽略删除失败
                
        except Exception as e:
            logger.error(f"解析文档失败: {file_path}, 错误: {e}", exc_info=True)
            raise
    
    async def parse_document_with_retry(
        self,
        file_path: str,
        file_type: str,
        storage: StorageInterface,
        max_retries: int = 3
    ) -> Optional[Dict[str, Any]]:
        """
        解析文档（带重试机制，异步）
        
        Args:
            file_path: 文件存储路径
            file_type: 文件类型
            storage: 存储接口
            max_retries: 最大重试次数
        
        Returns:
            解析结果，失败返回None
        """
        for attempt in range(max_retries):
            try:
                return await self.parse_document(file_path, file_type, storage)
            except Exception as e:
                logger.warning(f"解析文档失败（尝试 {attempt + 1}/{max_retries}）: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"解析文档最终失败: {file_path}")
                    return None
        
        return None

