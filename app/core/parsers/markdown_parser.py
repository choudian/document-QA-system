"""
Markdown文件解析器
"""
import logging
from pathlib import Path
from typing import Dict, Any
from app.core.parsers.parser_interface import ParserInterface
import re

logger = logging.getLogger(__name__)


class MarkdownParser(ParserInterface):
    """Markdown文件解析器"""
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """解析Markdown文件"""
        file = Path(file_path)
        
        if not file.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 读取文件内容
        try:
            content = file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                content = file.read_text(encoding="gbk")
            except UnicodeDecodeError:
                content = file.read_text(encoding="latin-1")
        
        # 去除BOM
        if content.startswith("\ufeff"):
            content = content[1:]
        
        # 提取标题（第一个#标题或文件名）
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip()[:500]
        else:
            title = file.stem[:500] if file.stem else "无标题"
        
        # 提取摘要（去除标题和代码块后的前200个字符）
        summary_content = re.sub(r"```[\s\S]*?```", "", content)  # 移除代码块
        summary_content = re.sub(r"^#+\s+.*$", "", summary_content, flags=re.MULTILINE)  # 移除标题
        summary = summary_content.strip()[:200] if summary_content.strip() else ""
        
        return {
            "content": content,
            "title": title,
            "summary": summary,
            "metadata": {}
        }
    
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """提取Markdown文件元数据"""
        file = Path(file_path)
        
        return {
            "page_count": None,
            "file_size": file.stat().st_size if file.exists() else 0,
        }

