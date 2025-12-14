"""
文档管理API
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List
from app.core.database import get_db
from app.api.v1.me import get_current_user
from app.schemas.document import (
    FolderCreate, FolderUpdate, FolderResponse,
    DocumentUploadRequest, DocumentUploadResponse, CheckDuplicateRequest, CheckDuplicateResponse,
    DocumentListResponse, DocumentDetailResponse, DocumentListQuery,
    DocumentVersionResponse, TagResponse, DocumentTagRequest, DocumentTagListResponse,
    DocumentConfigRequest, DocumentConfigResponse
)
from app.schemas.document_task import DocumentTaskResponse, DocumentTaskListResponse
from app.repositories.folder_repository import FolderRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.document_version_repository import DocumentVersionRepository
from app.repositories.document_config_repository import DocumentConfigRepository
from app.repositories.document_tag_repository import DocumentTagRepository
from app.repositories.config_repository import ConfigRepository
from app.services.folder_service import FolderService
from app.services.document_service import DocumentService
from app.services.storage_service import StorageService
from app.services.document_parser_service import DocumentParserService
from app.services.config_service import ConfigService
from app.core.permissions import require_permission
from app.models.user import User

router = APIRouter()


def _build_folder_service(db: Session) -> FolderService:
    """构建文件夹服务"""
    return FolderService(
        folder_repo=FolderRepository(db)
    )


def _build_document_service(db: Session) -> DocumentService:
    """构建文档服务"""
    return DocumentService(
        document_repo=DocumentRepository(db),
        document_version_repo=DocumentVersionRepository(db),
        document_config_repo=DocumentConfigRepository(db),
        folder_repo=FolderRepository(db),
        storage_service=StorageService(),
        parser_service=DocumentParserService(),
        config_service=ConfigService(ConfigRepository(db))
    )


# 文件夹接口
@router.post("/folders", response_model=FolderResponse, status_code=status.HTTP_201_CREATED)
def create_folder(
    folder: FolderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(require_permission("doc:folder:create"))
):
    """创建文件夹"""
    service = _build_folder_service(db)
    return service.create_folder(
        name=folder.name,
        parent_id=folder.parent_id,
        tenant_id=current_user.tenant_id or "",
        user_id=current_user.id
    )


@router.get("/folders", response_model=List[FolderResponse])
def list_folders(
    parent_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(require_permission("doc:folder:read"))
):
    """查询文件夹列表"""
    service = _build_folder_service(db)
    return service.list_folders(
        tenant_id=current_user.tenant_id or "",
        user_id=current_user.id,
        parent_id=parent_id
    )


@router.get("/folders/{folder_id}", response_model=FolderResponse)
def get_folder(
    folder_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(require_permission("doc:folder:read"))
):
    """查询文件夹详情"""
    service = _build_folder_service(db)
    return service.get_folder(folder_id, current_user.tenant_id or "", current_user.id)


@router.put("/folders/{folder_id}", response_model=FolderResponse)
def update_folder(
    folder_id: str,
    folder: FolderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(require_permission("doc:folder:update"))
):
    """重命名文件夹"""
    service = _build_folder_service(db)
    return service.update_folder(
        folder_id=folder_id,
        name=folder.name,
        tenant_id=current_user.tenant_id or "",
        user_id=current_user.id
    )


@router.delete("/folders/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_folder(
    folder_id: str,
    confirm_text: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(require_permission("doc:folder:delete"))
):
    """删除文件夹（需二次确认）"""
    service = _build_folder_service(db)
    service.delete_folder(
        folder_id=folder_id,
        tenant_id=current_user.tenant_id or "",
        user_id=current_user.id,
        confirm_text=confirm_text
    )
    return None


# 文档接口
@router.post("/check-duplicate", response_model=CheckDuplicateResponse)
def check_duplicate(
    payload: CheckDuplicateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(require_permission("doc:file:read"))
):
    """检查同名文件"""
    service = _build_document_service(db)
    existing = service.check_duplicate(
        filename=payload.filename,
        folder_id=payload.folder_id,
        tenant_id=current_user.tenant_id or "",
        user_id=current_user.id
    )
    
    if existing:
        return CheckDuplicateResponse(
            exists=True,
            document_id=existing.id,
            version=existing.version
        )
    return CheckDuplicateResponse(exists=False)


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    folder_id: Optional[str] = Form(None),
    chunk_size: Optional[int] = Form(None),
    chunk_overlap: Optional[int] = Form(None),
    split_method: Optional[str] = Form(None),
    split_keyword: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    _=Depends(require_permission("doc:file:upload"))
):
    """上传文档"""
    service = _build_document_service(db)
    
    # 读取文件内容
    file_content = await file.read()
    
    # 准备配置数据
    config_data = None
    if chunk_size or chunk_overlap or split_method or split_keyword:
        config_data = {
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "split_method": split_method,
            "split_keyword": split_keyword
        }
    
    # 上传文档
    document = await service.upload_document(
        file_content=file_content,
        filename=file.filename or "unknown",
        folder_id=folder_id,
        tenant_id=current_user.tenant_id or "",
        user_id=current_user.id,
        config_data=config_data,
        background_tasks=background_tasks
    )
    
    return DocumentUploadResponse(
        id=document.id,
        name=document.name,
        status=document.status,
        created_at=document.created_at
    )


@router.get("", response_model=List[DocumentListResponse])
def list_documents(
    folder_id: Optional[str] = None,
    status: Optional[str] = None,
    tag: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(require_permission("doc:file:read"))
):
    """查询文档列表（支持按标签筛选）"""
    service = _build_document_service(db)
    documents = service.list_documents(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id or "",
        folder_id=folder_id,
        status=status,
        tag=tag,
        skip=skip,
        limit=limit
    )
    return documents


# 标签接口（必须在 /{document_id} 路由之前定义，避免路由冲突）
@router.get("/tags", response_model=List[TagResponse])
def list_tags(
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(require_permission("doc:file:read"))
):
    """获取用户标签列表（用于自动补全）"""
    tag_repo = DocumentTagRepository(db)
    tags = tag_repo.list_tags_by_user(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id or "",
        search=search
    )
    return tags


# 文档详情接口（必须在标签接口之后，避免路由冲突）
@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(require_permission("doc:file:read"))
):
    """查询文档详情"""
    service = _build_document_service(db)
    document = service.get_document(document_id, current_user.tenant_id or "", current_user.id)
    
    # 获取文档配置
    from app.repositories.document_config_repository import DocumentConfigRepository
    config_repo = DocumentConfigRepository(db)
    config = config_repo.get_by_document_id(document_id)
    
    # 构建响应，确保 config 是单个对象而不是列表
    response_data = {
        "id": document.id,
        "tenant_id": document.tenant_id,
        "user_id": document.user_id,
        "folder_id": document.folder_id,
        "name": document.name,
        "original_name": document.original_name,
        "file_type": document.file_type,
        "mime_type": document.mime_type,
        "file_size": document.file_size,
        "file_hash": document.file_hash,
        "version": document.version,
        "status": document.status,
        "page_count": document.page_count,
        "title": document.title,
        "summary": document.summary,
        "created_at": document.created_at,
        "updated_at": document.updated_at,
        "config": DocumentConfigResponse.from_orm(config) if config else None
    }
    
    return DocumentDetailResponse(**response_data)


@router.post("/{document_id}/tags", status_code=status.HTTP_201_CREATED)
def add_tag_to_document(
    document_id: str,
    payload: DocumentTagRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(require_permission("doc:file:update"))
):
    """为文档添加标签（支持通过tag_id或tag_name）"""
    # 验证文档权限
    service = _build_document_service(db)
    document = service.get_document(document_id, current_user.tenant_id or "", current_user.id)
    
    tag_repo = DocumentTagRepository(db)
    tenant_id = current_user.tenant_id or ""
    user_id = current_user.id
    
    # 确定要使用的tag_id
    tag_id = None
    if payload.tag_id:
        # 如果提供了tag_id，直接使用
        tag_id = payload.tag_id
    elif payload.tag_name:
        # 如果提供了tag_name，获取或创建标签
        tag_name = payload.tag_name.strip()
        if not tag_name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="标签名称不能为空")
        if len(tag_name) > 20:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="标签名称不能超过20个字符")
        
        tag = tag_repo.get_or_create_tag(tag_name, user_id, tenant_id)
        tag_id = tag.id
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="必须提供tag_id或tag_name")
    
    # 添加标签到文档
    tag_repo.add_tag_to_document(document_id, tag_id)
    return {"message": "标签已添加"}


@router.delete("/{document_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_tag_from_document(
    document_id: str,
    tag_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(require_permission("doc:file:update"))
):
    """从文档移除标签"""
    # 验证文档权限
    service = _build_document_service(db)
    service.get_document(document_id, current_user.tenant_id or "", current_user.id)
    
    tag_repo = DocumentTagRepository(db)
    tag_repo.remove_tag_from_document(document_id, tag_id)
    return None


@router.get("/{document_id}/tags", response_model=DocumentTagListResponse)
def get_document_tags(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(require_permission("doc:file:read"))
):
    """获取文档的所有标签"""
    # 验证文档权限
    service = _build_document_service(db)
    service.get_document(document_id, current_user.tenant_id or "", current_user.id)
    
    tag_repo = DocumentTagRepository(db)
    tags = tag_repo.get_document_tags(document_id)
    return DocumentTagListResponse(tags=[TagResponse.from_orm(tag) for tag in tags])


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(require_permission("doc:file:delete"))
):
    """删除文档（软删除）"""
    service = _build_document_service(db)
    service.delete_document(document_id, current_user.tenant_id or "", current_user.id)
    return None


@router.post("/{document_id}/restore", status_code=status.HTTP_200_OK)
def restore_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(require_permission("doc:file:update"))
):
    """恢复软删除的文档"""
    service = _build_document_service(db)
    document = service.restore_document(document_id, current_user.tenant_id or "", current_user.id)
    
    # 获取文档配置
    config_repo = DocumentConfigRepository(db)
    config = config_repo.get_by_document_id(document_id)
    
    # 构建响应（与get_document保持一致）
    response_data = {
        "id": document.id,
        "tenant_id": document.tenant_id,
        "user_id": document.user_id,
        "folder_id": document.folder_id,
        "name": document.name,
        "original_name": document.original_name,
        "file_type": document.file_type,
        "mime_type": document.mime_type,
        "file_size": document.file_size,
        "file_hash": document.file_hash,
        "version": document.version,
        "status": document.status,
        "page_count": document.page_count,
        "title": document.title,
        "summary": document.summary,
        "created_at": document.created_at,
        "updated_at": document.updated_at,
        "config": DocumentConfigResponse.from_orm(config) if config else None
    }
    
    return DocumentDetailResponse(**response_data)


@router.get("/trash", response_model=List[DocumentListResponse])
def list_trash_documents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(require_permission("doc:file:read"))
):
    """查询回收站文档列表"""
    service = _build_document_service(db)
    documents = service.list_trash_documents(
        tenant_id=current_user.tenant_id or "",
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return documents


@router.get("/{document_id}/versions", response_model=List[DocumentVersionResponse])
def get_document_versions(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(require_permission("doc:file:read"))
):
    """获取文档版本历史"""
    service = _build_document_service(db)
    versions = service.get_document_versions(document_id, current_user.tenant_id or "", current_user.id)
    return versions


@router.delete("/{document_id}/versions/{version_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document_version(
    document_id: str,
    version_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(require_permission("doc:file:delete"))
):
    """删除指定版本（仅所有者）"""
    # 验证文档权限
    service = _build_document_service(db)
    document = service.get_document(document_id, current_user.tenant_id or "", current_user.id)
    
    # 验证版本是否存在
    version_repo = DocumentVersionRepository(db)
    version = version_repo.get_by_id(version_id)
    if not version or version.document_id != document_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="版本不存在")
    
    # 删除版本
    version_repo.delete(version_id)
    return None


@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(require_permission("doc:file:read"))
):
    """下载文档原文件"""
    import asyncio
    
    service = _build_document_service(db)
    document = service.get_document(document_id, current_user.tenant_id or "", current_user.id)
    
    # 获取存储服务
    from app.core.storage import get_storage
    storage = get_storage()
    
    # 读取文件
    file_content = await storage.read_file(document.storage_path)
    
    # 返回文件响应
    from fastapi.responses import Response
    return Response(
        content=file_content,
        media_type=document.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{document.original_name}"'
        }
    )


@router.get("/{document_id}/preview")
def preview_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(require_permission("doc:file:read"))
):
    """预览文档Markdown（预留接口）"""
    # 预留接口，暂时返回空响应
    return {"message": "预览功能待实现"}


@router.get("/config/recent", response_model=DocumentConfigResponse)
def get_recent_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(require_permission("doc:file:read"))
):
    """获取用户最近使用的配置"""
    from app.repositories.document_config_repository import DocumentConfigRepository
    config_repo = DocumentConfigRepository(db)
    recent_config = config_repo.get_user_recent_config(current_user.id)
    
    if not recent_config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="没有最近使用的配置")
    
    return DocumentConfigResponse.from_orm(recent_config)


# 待办表接口（占位实现）
@router.get("/tasks", response_model=DocumentTaskListResponse)
def list_document_tasks(
    task_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(require_permission("doc:file:read"))
):
    """
    查询文档任务列表（待办表）
    
    注意：此功能暂未实现，仅作为占位接口
    """
    from app.repositories.document_task_repository import DocumentTaskRepository
    from app.services.document_task_service import DocumentTaskService
    
    task_repo = DocumentTaskRepository(db)
    task_service = DocumentTaskService(task_repo)
    
    tasks = task_service.list_tasks(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id or "",
        task_type=task_type,
        skip=skip,
        limit=limit
    )
    
    return DocumentTaskListResponse(
        tasks=[DocumentTaskResponse.from_orm(task) for task in tasks],
        total=len(tasks)
    )


@router.get("/tasks/{task_id}", response_model=DocumentTaskResponse)
def get_document_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(require_permission("doc:file:read"))
):
    """
    获取文档任务详情
    
    注意：此功能暂未实现，仅作为占位接口
    """
    from app.repositories.document_task_repository import DocumentTaskRepository
    from app.services.document_task_service import DocumentTaskService
    
    task_repo = DocumentTaskRepository(db)
    task_service = DocumentTaskService(task_repo)
    
    task = task_service.get_task(
        task_id=task_id,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id or ""
    )
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    return DocumentTaskResponse.from_orm(task)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(require_permission("doc:file:delete"))
):
    """
    删除文档任务
    
    注意：此功能暂未实现，仅作为占位接口
    """
    from app.repositories.document_task_repository import DocumentTaskRepository
    from app.services.document_task_service import DocumentTaskService
    
    task_repo = DocumentTaskRepository(db)
    task_service = DocumentTaskService(task_repo)
    
    success = task_service.delete_task(
        task_id=task_id,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id or ""
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在或无权删除"
        )
    
    return None

