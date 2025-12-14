"""
文档解析器
"""
from app.core.parsers.parser_interface import ParserInterface
from app.core.parsers.parser_factory import ParserFactory, get_parser
from app.core.parsers.text_parser import TextParser
from app.core.parsers.markdown_parser import MarkdownParser
from app.core.parsers.pdf_parser import PDFParser
from app.core.parsers.word_parser import WordParser

__all__ = [
    "ParserInterface", "ParserFactory", "get_parser",
    "TextParser", "MarkdownParser", "PDFParser", "WordParser"
]

