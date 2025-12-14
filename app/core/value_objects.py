"""
值对象定义（Value Objects）
"""
from typing import Optional
from dataclasses import dataclass
from enum import Enum


class DocumentStatus(str, Enum):
    """文档状态枚举"""
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    PARSING = "parsing"
    VECTORIZING = "vectorizing"
    COMPLETED = "completed"
    UPLOAD_FAILED = "upload_failed"
    PARSE_FAILED = "parse_failed"
    VECTORIZE_FAILED = "vectorize_failed"
    
    @classmethod
    def is_processing(cls, status: str) -> bool:
        """判断是否正在处理中"""
        return status in [cls.UPLOADING, cls.PARSING, cls.VECTORIZING]
    
    @classmethod
    def is_failed(cls, status: str) -> bool:
        """判断是否失败"""
        return status in [cls.UPLOAD_FAILED, cls.PARSE_FAILED, cls.VECTORIZE_FAILED]


@dataclass
class FileUploadConfig:
    """文件上传配置值对象"""
    allowed_types: list[str]
    max_size_mb: int
    
    @property
    def max_size_bytes(self) -> int:
        """最大文件大小（字节）"""
        return self.max_size_mb * 1024 * 1024
    
    def validate_file_type(self, file_type: str) -> bool:
        """验证文件类型"""
        return file_type in self.allowed_types
    
    def validate_file_size(self, file_size: int) -> bool:
        """验证文件大小"""
        return file_size <= self.max_size_bytes


@dataclass
class ChunkConfig:
    """文本切分配置值对象"""
    chunk_size: int
    chunk_overlap: int
    split_method: str
    split_keyword: Optional[str] = None
    
    def validate(self) -> None:
        """验证配置有效性"""
        if self.chunk_size <= 0:
            raise ValueError("chunk_size必须大于0")
        if self.chunk_overlap < 0:
            raise ValueError("chunk_overlap不能小于0")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap不能大于等于chunk_size")
        if self.split_method == "keyword" and not self.split_keyword:
            raise ValueError("按关键字切分时，split_keyword不能为空")


@dataclass
class DocumentQuery:
    """文档查询值对象"""
    tenant_id: str
    user_id: str
    folder_id: Optional[str] = None
    status: Optional[str] = None
    tag: Optional[str] = None
    skip: int = 0
    limit: int = 100
    
    def validate(self) -> None:
        """验证查询参数"""
        if self.skip < 0:
            raise ValueError("skip不能小于0")
        if self.limit <= 0 or self.limit > 1000:
            raise ValueError("limit必须在1-1000之间")

