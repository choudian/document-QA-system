"""
文档任务相关Schema
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class DocumentTaskResponse(BaseModel):
    """文档任务响应"""
    id: str
    document_id: str
    tenant_id: str
    user_id: str
    task_type: str = Field(..., description="任务类型：parse_failed/vectorize_failed")
    reason: Optional[str] = None
    retries: int = Field(default=0, description="重试次数")
    task_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DocumentTaskListResponse(BaseModel):
    """文档任务列表响应"""
    tasks: list[DocumentTaskResponse]
    total: int

