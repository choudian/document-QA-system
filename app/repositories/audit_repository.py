"""
审计日志仓储
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from datetime import datetime
from app.models.audit_log import AuditLog


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create_audit_log(self, log_data: dict) -> AuditLog:
        """创建审计日志"""
        audit_log = AuditLog(**log_data)
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)
        return audit_log
    
    def list_audit_logs(
        self,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        method: Optional[str] = None,
        path: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[AuditLog], int]:
        """
        查询审计日志列表
        
        Returns:
            (日志列表, 总数)
        """
        query = self.db.query(AuditLog)
        
        # 构建查询条件
        conditions = []
        
        if user_id:
            conditions.append(AuditLog.user_id == user_id)
        
        if tenant_id:
            conditions.append(AuditLog.tenant_id == tenant_id)
        
        if method:
            conditions.append(AuditLog.method == method)
        
        if path:
            conditions.append(AuditLog.path.like(f"%{path}%"))
        
        if start_time:
            conditions.append(AuditLog.created_at >= start_time)
        
        if end_time:
            conditions.append(AuditLog.created_at <= end_time)
        
        if conditions:
            query = query.filter(and_(*conditions))
        
        # 获取总数
        total = query.count()
        
        # 分页查询
        logs = (
            query.order_by(desc(AuditLog.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        
        return logs, total
    
    def get_audit_log_by_id(self, log_id: str) -> Optional[AuditLog]:
        """根据ID获取审计日志"""
        return self.db.query(AuditLog).filter(AuditLog.id == log_id).first()
    
    def commit(self):
        """提交事务"""
        self.db.commit()
    
    def rollback(self):
        """回滚事务"""
        self.db.rollback()

