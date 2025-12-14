"""
文件系统存储实现
"""
import os
import logging
from pathlib import Path
from typing import Optional
from app.core.storage.storage_interface import StorageInterface
from app.core.config import settings

logger = logging.getLogger(__name__)


class FilesystemStorage(StorageInterface):
    """文件系统存储实现"""
    
    def __init__(self, base_path: Optional[str] = None):
        """
        初始化文件系统存储
        
        Args:
            base_path: 基础存储路径，默认为 ./storage
        """
        self.base_path = Path(base_path or getattr(settings, "STORAGE_BASE_PATH", "./storage"))
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"文件系统存储初始化，基础路径: {self.base_path.absolute()}")
    
    async def save_file(self, path: str, content: bytes) -> str:
        """保存文件"""
        full_path = self.base_path / path
        
        # 创建目录（使用线程池执行同步操作）
        import asyncio
        await asyncio.to_thread(full_path.parent.mkdir, parents=True, exist_ok=True)
        
        # 写入文件（使用线程池执行同步操作）
        await asyncio.to_thread(full_path.write_bytes, content)
        
        logger.debug(f"文件已保存: {full_path}")
        return str(full_path.relative_to(self.base_path))
    
    async def read_file(self, path: str) -> bytes:
        """读取文件"""
        full_path = self.base_path / path
        
        if not full_path.exists():
            raise FileNotFoundError(f"文件不存在: {full_path}")
        
        # 使用线程池执行同步文件读取操作
        import asyncio
        return await asyncio.to_thread(full_path.read_bytes)
    
    async def delete_file(self, path: str) -> bool:
        """删除文件"""
        full_path = self.base_path / path
        
        if not full_path.exists():
            logger.warning(f"文件不存在，无法删除: {full_path}")
            return False
        
        try:
            # 使用线程池执行同步文件删除操作
            import asyncio
            await asyncio.to_thread(full_path.unlink)
            logger.debug(f"文件已删除: {full_path}")
            return True
        except Exception as e:
            logger.error(f"删除文件失败: {full_path}, 错误: {e}")
            return False
    
    async def file_exists(self, path: str) -> bool:
        """检查文件是否存在"""
        full_path = self.base_path / path
        return full_path.exists()
    
    def generate_path(self, tenant_id: str, user_id: str, folder_path: str, filename: str) -> str:
        """
        生成文件存储路径
        
        路径格式: {tenant_id}/{user_id}/{folder_path}/{filename}
        """
        # 清理路径，防止路径遍历攻击
        folder_path = folder_path.strip("/") if folder_path else ""
        filename = os.path.basename(filename)  # 只取文件名，防止路径遍历
        
        if folder_path:
            path = f"{tenant_id}/{user_id}/{folder_path}/{filename}"
        else:
            path = f"{tenant_id}/{user_id}/{filename}"
        
        return path
    
    def generate_url(self, path: str, public: bool = False) -> str:
        """
        生成文件访问URL
        
        注意：文件系统存储默认不支持直接URL访问，这里返回相对路径
        实际部署时可以通过Nginx等反向代理提供文件访问
        """
        if public:
            # 公开访问URL（需要配置静态文件服务）
            return f"/storage/{path}"
        else:
            # 受控访问URL（需要通过API验证权限）
            return f"/api/v1/documents/files/{path}"

