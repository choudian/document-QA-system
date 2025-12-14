"""
PDF文件解析器
"""
import logging
from pathlib import Path
from typing import Dict, Any
from app.core.parsers.parser_interface import ParserInterface

logger = logging.getLogger(__name__)

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logger.warning("PyPDF2未安装，PDF解析功能不可用")


class PDFParser(ParserInterface):
    """PDF文件解析器（使用PyPDF2）"""
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """解析PDF文件为Markdown"""
        if not PDF_AVAILABLE:
            raise ImportError("PyPDF2未安装，无法解析PDF文件。请运行: pip install PyPDF2")
        
        file = Path(file_path)
        
        if not file.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 读取PDF
        with open(file_path, "rb") as f:
            pdf_reader = PyPDF2.PdfReader(f)
            
            # 提取所有页面的文本
            pages_text = []
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    text = page.extract_text()
                    if text.strip():
                        pages_text.append(f"## 第 {page_num + 1} 页\n\n{text}\n\n")
                except Exception as e:
                    logger.warning(f"提取第 {page_num + 1} 页文本失败: {e}")
            
            content = "\n".join(pages_text)
            
            # 提取标题（第一页的第一行或文件名）
            first_page_text = pages_text[0] if pages_text else ""
            title_lines = [line.strip() for line in first_page_text.split("\n") if line.strip() and not line.startswith("#")]
            title = title_lines[0][:500] if title_lines else file.stem[:500] if file.stem else "无标题"
            
            # 提取摘要（第一页的前200个字符）
            summary_text = first_page_text.replace("## 第 1 页\n\n", "").strip()
            summary = summary_text[:200] if summary_text else ""
            
            return {
                "content": content,
                "title": title,
                "summary": summary,
                "metadata": {
                    "page_count": len(pdf_reader.pages)
                }
            }
    
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """提取PDF文件元数据"""
        if not PDF_AVAILABLE:
            return {"page_count": None, "file_size": 0}
        
        file = Path(file_path)
        
        try:
            with open(file_path, "rb") as f:
                pdf_reader = PyPDF2.PdfReader(f)
                return {
                    "page_count": len(pdf_reader.pages),
                    "file_size": file.stat().st_size if file.exists() else 0,
                }
        except Exception as e:
            logger.error(f"提取PDF元数据失败: {e}")
            return {
                "page_count": None,
                "file_size": file.stat().st_size if file.exists() else 0,
            }

