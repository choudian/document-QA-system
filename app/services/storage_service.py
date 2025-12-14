"""
存储服务
"""
import hashlib
import logging
from typing import Optional
from app.core.storage import get_storage, StorageInterface
from app.core.storage.storage_interface import StorageInterface

logger = logging.getLogger(__name__)


class StorageService:
    """存储服务（封装存储抽象层）"""
    
    def __init__(self, storage: Optional[StorageInterface] = None):
        self.storage = storage or get_storage()
    
    async def save_file(
        self,
        content: bytes,
        tenant_id: str,
        user_id: str,
        folder_path: str,
        filename: str
    ) -> str:
        """
        保存文件
        
        Returns:
            存储路径（相对路径）
        """
        storage_path = self.storage.generate_path(tenant_id, user_id, folder_path, filename)
        await self.storage.save_file(storage_path, content)
        return storage_path
    
    async def read_file(self, path: str) -> bytes:
        """读取文件"""
        return await self.storage.read_file(path)
    
    async def delete_file(self, path: str) -> bool:
        """删除文件"""
        return await self.storage.delete_file(path)
    
    async def file_exists(self, path: str) -> bool:
        """检查文件是否存在"""
        return await self.storage.file_exists(path)
    
    def generate_file_hash(self, content: bytes) -> str:
        """生成文件哈希值（SHA256）"""
        return hashlib.sha256(content).hexdigest()
    
    def generate_url(self, path: str, public: bool = False) -> str:
        """生成文件访问URL"""
        return self.storage.generate_url(path, public)

