"""
TXT文件解析器
"""
import logging
from pathlib import Path
from typing import Dict, Any
from app.core.parsers.parser_interface import ParserInterface

logger = logging.getLogger(__name__)


class TextParser(ParserInterface):
    """TXT文件解析器"""
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """解析TXT文件为Markdown"""
        file = Path(file_path)
        
        if not file.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 读取文件内容
        try:
            # 尝试UTF-8编码
            content = file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                content = file.read_text(encoding="gbk")
            except UnicodeDecodeError:
                content = file.read_text(encoding="latin-1")
        
        # 去除BOM
        if content.startswith("\ufeff"):
            content = content[1:]
        
        # 提取标题（第一行或前100个字符）
        lines = content.strip().split("\n")
        title = lines[0].strip()[:500] if lines else "无标题"
        
        # 提取摘要（前200个字符）
        summary = content.strip()[:200] if content.strip() else ""
        
        # 转换为Markdown格式（简单处理，保持原样）
        markdown_content = content
        
        return {
            "content": markdown_content,
            "title": title,
            "summary": summary,
            "metadata": {}
        }
    
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """提取TXT文件元数据"""
        file = Path(file_path)
        
        return {
            "page_count": None,
            "file_size": file.stat().st_size if file.exists() else 0,
        }

