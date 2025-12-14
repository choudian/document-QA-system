"""
解析器接口抽象
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class ParserInterface(ABC):
    """解析器接口抽象类"""
    
    @abstractmethod
    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        解析文件
        
        Args:
            file_path: 文件路径
        
        Returns:
            解析结果字典，包含：
            - content: Markdown格式的内容
            - title: 文档标题
            - summary: 摘要
            - metadata: 元数据（页数、作者等）
        """
        pass
    
    @abstractmethod
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        提取文件元数据
        
        Args:
            file_path: 文件路径
        
        Returns:
            元数据字典，包含：
            - page_count: 页数（PDF/Word）
            - author: 作者
            - created_at: 创建时间
            - 其他文件特定元数据
        """
        pass

