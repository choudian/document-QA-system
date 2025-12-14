"""
解析器工厂
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from app.core.parsers.parser_interface import ParserInterface
from app.core.parsers.text_parser import TextParser
from app.core.parsers.markdown_parser import MarkdownParser
from app.core.parsers.pdf_parser import PDFParser
from app.core.parsers.word_parser import WordParser

logger = logging.getLogger(__name__)


class ParserFactory:
    """解析器工厂类"""
    
    # 文件类型到解析器的映射
    _parser_map: Dict[str, type] = {
        "txt": TextParser,
        "md": MarkdownParser,
        "markdown": MarkdownParser,
        "pdf": PDFParser,
        "doc": WordParser,
        "docx": WordParser,
    }
    
    @classmethod
    def get_parser(cls, file_path: str) -> ParserInterface:
        """
        根据文件路径获取对应的解析器
        
        Args:
            file_path: 文件路径
        
        Returns:
            解析器实例
        """
        file = Path(file_path)
        extension = file.suffix.lower().lstrip(".")
        
        parser_class = cls._parser_map.get(extension)
        
        if parser_class is None:
            raise ValueError(f"不支持的文件类型: {extension}")
        
        return parser_class()
    
    @classmethod
    def get_parser_by_type(cls, file_type: str) -> ParserInterface:
        """
        根据文件类型获取对应的解析器
        
        Args:
            file_type: 文件类型（txt/md/pdf/word）
        
        Returns:
            解析器实例
        """
        type_map = {
            "txt": TextParser,
            "md": MarkdownParser,
            "markdown": MarkdownParser,
            "pdf": PDFParser,
            "word": WordParser,
            "doc": WordParser,
            "docx": WordParser,
        }
        
        parser_class = type_map.get(file_type.lower())
        
        if parser_class is None:
            raise ValueError(f"不支持的文件类型: {file_type}")
        
        return parser_class()
    
    @classmethod
    def is_supported(cls, file_path: str) -> bool:
        """
        检查文件类型是否支持
        
        Args:
            file_path: 文件路径
        
        Returns:
            是否支持
        """
        file = Path(file_path)
        extension = file.suffix.lower().lstrip(".")
        return extension in cls._parser_map
    
    @classmethod
    def get_supported_types(cls) -> list:
        """
        获取支持的文件类型列表
        
        Returns:
            支持的文件类型列表
        """
        return list(cls._parser_map.keys())


def get_parser(file_path: str) -> ParserInterface:
    """
    获取解析器（便捷函数）
    
    Args:
        file_path: 文件路径
    
    Returns:
        解析器实例
    """
    return ParserFactory.get_parser(file_path)

