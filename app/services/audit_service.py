"""
审计日志服务
"""
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from datetime import datetime
from app.repositories.audit_repository import AuditRepository
from app.models.audit_log import AuditLog


class AuditService:
    def __init__(self, db: Session):
        self.audit_repo = AuditRepository(db)
        self.db = db
    
    def list_logs(
        self,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        method: Optional[str] = None,
        path: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[AuditLog], int]:
        """
        查询审计日志列表
        
        Returns:
            (日志列表, 总数)
        """
        return self.audit_repo.list_audit_logs(
            user_id=user_id,
            tenant_id=tenant_id,
            method=method,
            path=path,
            start_time=start_time,
            end_time=end_time,
            page=page,
            page_size=page_size,
        )
    
    def get_log_by_id(self, log_id: str) -> Optional[AuditLog]:
        """根据ID获取审计日志详情"""
        return self.audit_repo.get_audit_log_by_id(log_id)

