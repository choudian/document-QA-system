"""
存储工厂
"""
import logging
from typing import Optional
from app.core.storage.storage_interface import StorageInterface
from app.core.storage.filesystem_storage import FilesystemStorage
from app.core.config import settings

logger = logging.getLogger(__name__)

# 全局存储实例
_storage_instance: Optional[StorageInterface] = None


class StorageFactory:
    """存储工厂类"""
    
    @staticmethod
    def create_storage(storage_type: str = "filesystem", **kwargs) -> StorageInterface:
        """
        创建存储实例
        
        Args:
            storage_type: 存储类型（filesystem/s3/oss/minio）
            **kwargs: 存储配置参数
        
        Returns:
            存储实例
        """
        if storage_type == "filesystem":
            base_path = kwargs.get("base_path") or getattr(settings, "STORAGE_BASE_PATH", "./storage")
            return FilesystemStorage(base_path=base_path)
        elif storage_type == "s3":
            # 预留：S3存储实现
            raise NotImplementedError("S3存储暂未实现")
        elif storage_type == "oss":
            # 预留：OSS存储实现
            raise NotImplementedError("OSS存储暂未实现")
        elif storage_type == "minio":
            # 预留：MinIO存储实现
            raise NotImplementedError("MinIO存储暂未实现")
        else:
            raise ValueError(f"不支持的存储类型: {storage_type}")
    
    @staticmethod
    def get_default_storage() -> StorageInterface:
        """
        获取默认存储实例（单例模式）
        
        Returns:
            默认存储实例
        """
        global _storage_instance
        
        if _storage_instance is None:
            storage_type = getattr(settings, "STORAGE_TYPE", "filesystem")
            _storage_instance = StorageFactory.create_storage(storage_type)
            logger.info(f"创建默认存储实例，类型: {storage_type}")
        
        return _storage_instance


def get_storage() -> StorageInterface:
    """
    获取存储实例（便捷函数）
    
    Returns:
        存储实例
    """
    return StorageFactory.get_default_storage()

