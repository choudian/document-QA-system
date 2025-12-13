"""
审计日志API
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.core.database import get_db
from app.api.v1.me import get_current_user
from app.models.user import User
from app.services.audit_service import AuditService
from app.schemas.audit_log import AuditLogResponse, AuditLogListResponse
from app.core.permissions import require_permission

router = APIRouter()


def _build_service(db: Session) -> AuditService:
    """构建审计日志服务"""
    return AuditService(db)


@router.get("", response_model=AuditLogListResponse)
def list_audit_logs(
    user_id: Optional[str] = Query(None, description="用户ID"),
    tenant_id: Optional[str] = Query(None, description="租户ID"),
    method: Optional[str] = Query(None, description="HTTP方法"),
    path: Optional[str] = Query(None, description="请求路径（模糊匹配）"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(require_permission("system:audit:read")),
):
    """
    查询审计日志列表
    只有系统管理员和租户管理员可以访问
    """
    # 权限检查：只有系统管理员和租户管理员可以访问
    if not current_user.is_system_admin and not current_user.is_tenant_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有系统管理员和租户管理员可以查看审计日志"
        )
    
    # 租户管理员只能查看自己租户的日志
    if current_user.is_tenant_admin and not current_user.is_system_admin:
        if tenant_id and tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="不能查看其他租户的审计日志"
            )
        # 强制使用当前用户的租户ID
        tenant_id = current_user.tenant_id
    
    service = _build_service(db)
    logs, total = service.list_logs(
        user_id=user_id,
        tenant_id=tenant_id,
        method=method,
        path=path,
        start_time=start_time,
        end_time=end_time,
        page=page,
        page_size=page_size,
    )
    
    return AuditLogListResponse(
        items=[AuditLogResponse.from_orm(log) for log in logs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{log_id}", response_model=AuditLogResponse)
def get_audit_log(
    log_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(require_permission("system:audit:read")),
):
    """
    获取单条审计日志详情
    只有系统管理员和租户管理员可以访问
    """
    # 权限检查：只有系统管理员和租户管理员可以访问
    if not current_user.is_system_admin and not current_user.is_tenant_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有系统管理员和租户管理员可以查看审计日志"
        )
    
    service = _build_service(db)
    log = service.get_log_by_id(log_id)
    
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="审计日志不存在"
        )
    
    # 租户管理员只能查看自己租户的日志
    if current_user.is_tenant_admin and not current_user.is_system_admin:
        if log.tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="不能查看其他租户的审计日志"
            )
    
    return AuditLogResponse.from_orm(log)

