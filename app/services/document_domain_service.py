"""
文档领域服务（Domain Service）
处理跨实体的业务逻辑
"""
import logging
from typing import Optional, Dict, Any
from app.core.value_objects import FileUploadConfig, ChunkConfig
from app.core.exceptions import FileValidationException
from app.services.config_service import ConfigService

logger = logging.getLogger(__name__)


class DocumentDomainService:
    """文档领域服务"""
    
    def __init__(self, config_service: ConfigService):
        self.config_service = config_service
    
    def get_upload_config(self, tenant_id: str) -> FileUploadConfig:
        """获取上传配置（系统/租户级）"""
        configs = self.config_service.list_scope_configs("tenant", tenant_id)
        upload_config = configs.get("doc", {}).get("upload", {})
        
        if not upload_config:
            # 使用系统默认配置
            configs = self.config_service.list_scope_configs("system", None)
            upload_config = configs.get("doc", {}).get("upload", {
                "upload_types": ["txt", "md", "pdf", "word"],
                "max_file_size_mb": 50
            })
        
        return FileUploadConfig(
            allowed_types=upload_config.get("upload_types", ["txt", "md", "pdf", "word"]),
            max_size_mb=upload_config.get("max_file_size_mb", 50)
        )
    
    def get_chunk_config(self, tenant_id: str) -> ChunkConfig:
        """获取文本切分配置（系统/租户级）"""
        configs = self.config_service.list_scope_configs("tenant", tenant_id)
        chunk_config = configs.get("doc", {}).get("chunk", {})
        
        if not chunk_config:
            # 使用系统默认配置
            configs = self.config_service.list_scope_configs("system", None)
            chunk_config = configs.get("doc", {}).get("chunk", {
                "strategy": "fixed",
                "size": 400,
                "overlap": 100
            })
        
        return ChunkConfig(
            chunk_size=chunk_config.get("size", 400),
            chunk_overlap=chunk_config.get("overlap", 100),
            split_method=chunk_config.get("strategy", "fixed"),
            split_keyword=chunk_config.get("split_keyword")
        )
    
    def validate_file(self, filename: str, file_content: bytes, upload_config: FileUploadConfig) -> tuple[str, str]:
        """
        验证文件
        
        Returns:
            (file_type, mime_type)
        """
        # 验证文件大小
        if not upload_config.validate_file_size(len(file_content)):
            raise FileValidationException(
                f"文件大小超过限制（最大 {upload_config.max_size_mb}MB）"
            )
        
        # 验证文件类型
        file_ext = filename.split(".")[-1].lower() if "." in filename else ""
        type_map = {
            "txt": "txt",
            "md": "md",
            "markdown": "md",
            "pdf": "pdf",
            "doc": "word",
            "docx": "word"
        }
        file_type = type_map.get(file_ext)
        
        if not file_type or not upload_config.validate_file_type(file_type):
            raise FileValidationException(
                f"不支持的文件类型，允许的类型: {', '.join(upload_config.allowed_types)}"
            )
        
        # 确定MIME类型
        mime_map = {
            "txt": "text/plain",
            "md": "text/markdown",
            "pdf": "application/pdf",
            "word": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        }
        mime_type = mime_map.get(file_type, "application/octet-stream")
        
        return file_type, mime_type

