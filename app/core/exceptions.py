"""
领域异常定义
"""
from fastapi import HTTPException, status


class DomainException(HTTPException):
    """领域异常基类"""
    
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


class DocumentNotFoundException(DomainException):
    """文档不存在异常"""
    
    def __init__(self, document_id: str):
        super().__init__(
            detail=f"文档不存在: {document_id}",
            status_code=status.HTTP_404_NOT_FOUND
        )


class DocumentPermissionDeniedException(DomainException):
    """文档权限不足异常"""
    
    def __init__(self, document_id: str):
        super().__init__(
            detail=f"无权访问该文档: {document_id}",
            status_code=status.HTTP_403_FORBIDDEN
        )


class DocumentProcessingException(DomainException):
    """文档处理中异常"""
    
    def __init__(self, document_id: str, current_status: str):
        super().__init__(
            detail=f"文档正在处理中（状态: {current_status}），请稍后再试",
            status_code=status.HTTP_400_BAD_REQUEST
        )


class FolderNotFoundException(DomainException):
    """文件夹不存在异常"""
    
    def __init__(self, folder_id: str):
        super().__init__(
            detail=f"文件夹不存在: {folder_id}",
            status_code=status.HTTP_404_NOT_FOUND
        )


class FolderPermissionDeniedException(DomainException):
    """文件夹权限不足异常"""
    
    def __init__(self, folder_id: str):
        super().__init__(
            detail=f"无权访问该文件夹: {folder_id}",
            status_code=status.HTTP_403_FORBIDDEN
        )


class FolderLevelExceededException(DomainException):
    """文件夹层级超出限制异常"""
    
    def __init__(self, max_level: int = 2):
        super().__init__(
            detail=f"文件夹层级不能超过{max_level}层（根目录/1级）",
            status_code=status.HTTP_400_BAD_REQUEST
        )


class FileValidationException(DomainException):
    """文件验证异常"""
    
    def __init__(self, detail: str):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class ConversationNotFoundException(DomainException):
    """会话不存在异常"""
    
    def __init__(self, conversation_id: str):
        super().__init__(
            detail=f"会话不存在: {conversation_id}",
            status_code=status.HTTP_404_NOT_FOUND
        )


class ConversationPermissionDeniedException(DomainException):
    """会话权限不足异常"""
    
    def __init__(self, conversation_id: str):
        super().__init__(
            detail=f"无权访问该会话: {conversation_id}",
            status_code=status.HTTP_403_FORBIDDEN
        )


class MessageNotFoundException(DomainException):
    """消息不存在异常"""
    
    def __init__(self, message_id: str):
        super().__init__(
            detail=f"消息不存在: {message_id}",
            status_code=status.HTTP_404_NOT_FOUND
        )


class MessagePermissionDeniedException(DomainException):
    """消息权限不足异常"""
    
    def __init__(self, message_id: str):
        super().__init__(
            detail=f"无权访问该消息: {message_id}",
            status_code=status.HTTP_403_FORBIDDEN
        )

