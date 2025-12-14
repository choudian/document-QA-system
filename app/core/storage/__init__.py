"""
存储抽象层
"""
from app.core.storage.storage_interface import StorageInterface
from app.core.storage.filesystem_storage import FilesystemStorage
from app.core.storage.storage_factory import StorageFactory, get_storage

__all__ = ["StorageInterface", "FilesystemStorage", "StorageFactory", "get_storage"]

