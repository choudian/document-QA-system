"""
文档管理Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# 文件夹相关Schema
class FolderCreate(BaseModel):
    """创建文件夹请求"""
    name: str = Field(..., min_length=1, max_length=255, description="文件夹名称")
    parent_id: Optional[str] = Field(None, description="父文件夹ID（为空表示根目录）")


class FolderUpdate(BaseModel):
    """更新文件夹请求"""
    name: str = Field(..., min_length=1, max_length=255, description="文件夹名称")


class FolderResponse(BaseModel):
    """文件夹响应"""
    id: str
    tenant_id: str
    user_id: str
    parent_id: Optional[str]
    name: str
    path: str
    level: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# 文档配置相关Schema
class DocumentConfigRequest(BaseModel):
    """文档配置请求"""
    chunk_size: Optional[int] = Field(None, ge=1, le=5000, description="文本切分块大小")
    chunk_overlap: Optional[int] = Field(None, ge=0, le=4000, description="文本切分重叠大小")
    split_method: Optional[str] = Field(None, description="切分方法：length/paragraph/keyword")
    split_keyword: Optional[str] = Field(None, max_length=100, description="切分关键字（当split_method=keyword时使用）")


class DocumentConfigResponse(BaseModel):
    """文档配置响应"""
    chunk_size: int
    chunk_overlap: int
    split_method: str
    split_keyword: Optional[str]
    
    class Config:
        from_attributes = True


# 文档上传相关Schema
class DocumentUploadRequest(BaseModel):
    """文档上传请求（表单数据）"""
    folder_id: Optional[str] = Field(None, description="所属文件夹ID")
    chunk_size: Optional[int] = Field(None, ge=1, le=5000, description="文本切分块大小")
    chunk_overlap: Optional[int] = Field(None, ge=0, le=4000, description="文本切分重叠大小")
    split_method: Optional[str] = Field(None, description="切分方法：length/paragraph/keyword")
    split_keyword: Optional[str] = Field(None, max_length=100, description="切分关键字")


class DocumentUploadResponse(BaseModel):
    """文档上传响应"""
    id: str
    name: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class CheckDuplicateRequest(BaseModel):
    """检查同名文件请求"""
    filename: str = Field(..., description="文件名")
    folder_id: Optional[str] = Field(None, description="所属文件夹ID")


class CheckDuplicateResponse(BaseModel):
    """检查同名文件响应"""
    exists: bool
    document_id: Optional[str] = None
    version: Optional[str] = None


# 文档列表和详情Schema
class DocumentListResponse(BaseModel):
    """文档列表响应"""
    id: str
    name: str
    original_name: str
    file_type: str
    file_size: int
    status: str
    title: Optional[str]
    page_count: Optional[int]
    folder_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DocumentDetailResponse(BaseModel):
    """文档详情响应"""
    id: str
    tenant_id: str
    user_id: str
    folder_id: Optional[str]
    name: str
    original_name: str
    file_type: str
    mime_type: str
    file_size: int
    file_hash: str
    version: str
    status: str
    page_count: Optional[int]
    title: Optional[str]
    summary: Optional[str]
    created_at: datetime
    updated_at: datetime
    config: Optional[DocumentConfigResponse] = None
    
    class Config:
        from_attributes = True


# 文档版本Schema
class DocumentVersionResponse(BaseModel):
    """文档版本响应"""
    id: str
    document_id: str
    version: str
    operator_id: str
    remark: Optional[str]
    is_current: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# 标签相关Schema
class TagCreate(BaseModel):
    """创建标签请求"""
    name: str = Field(..., min_length=1, max_length=20, description="标签名称（20字以内）")


class TagResponse(BaseModel):
    """标签响应"""
    id: str
    name: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class DocumentTagRequest(BaseModel):
    """为文档添加标签请求"""
    tag_id: Optional[str] = Field(None, description="标签ID（如果提供，直接使用）")
    tag_name: Optional[str] = Field(None, description="标签名称（如果提供，自动创建或查找）")


class DocumentTagListResponse(BaseModel):
    """文档标签列表响应"""
    tags: List[TagResponse]


# 文档列表查询参数
class DocumentListQuery(BaseModel):
    """文档列表查询参数"""
    folder_id: Optional[str] = None
    status: Optional[str] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)

