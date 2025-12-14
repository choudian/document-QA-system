"""
存储接口抽象
"""
from abc import ABC, abstractmethod
from typing import Optional


class StorageInterface(ABC):
    """存储接口抽象类"""
    
    @abstractmethod
    async def save_file(self, path: str, content: bytes) -> str:
        """
        保存文件
        
        Args:
            path: 文件路径（相对路径）
            content: 文件内容（字节）
        
        Returns:
            保存后的完整路径
        """
        pass
    
    @abstractmethod
    async def read_file(self, path: str) -> bytes:
        """
        读取文件
        
        Args:
            path: 文件路径（相对路径）
        
        Returns:
            文件内容（字节）
        """
        pass
    
    @abstractmethod
    async def delete_file(self, path: str) -> bool:
        """
        删除文件
        
        Args:
            path: 文件路径（相对路径）
        
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def file_exists(self, path: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            path: 文件路径（相对路径）
        
        Returns:
            文件是否存在
        """
        pass
    
    @abstractmethod
    def generate_path(self, tenant_id: str, user_id: str, folder_path: str, filename: str) -> str:
        """
        生成文件存储路径
        
        Args:
            tenant_id: 租户ID
            user_id: 用户ID
            folder_path: 文件夹路径（相对路径，可为空）
            filename: 文件名
        
        Returns:
            完整的存储路径（相对路径）
        """
        pass
    
    @abstractmethod
    def generate_url(self, path: str, public: bool = False) -> str:
        """
        生成文件访问URL
        
        Args:
            path: 文件路径（相对路径）
            public: 是否公开访问
        
        Returns:
            文件访问URL
        """
        pass

