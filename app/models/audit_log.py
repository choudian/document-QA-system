"""
审计日志模型
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, Index
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class AuditLog(Base):
    """审计日志实体"""
    __tablename__ = "audit_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), comment="日志ID")
    user_id = Column(String, nullable=True, comment="用户ID（未登录用户为空）")
    tenant_id = Column(String, nullable=True, comment="租户ID")
    method = Column(String(10), nullable=False, comment="HTTP方法")
    path = Column(String(500), nullable=False, comment="请求路径")
    query_params = Column(Text, nullable=True, comment="查询参数（JSON）")
    request_body = Column(Text, nullable=True, comment="请求体（JSON，已脱敏）")
    response_status = Column(Integer, nullable=False, comment="响应状态码")
    response_body = Column(Text, nullable=True, comment="响应体（JSON，已脱敏）")
    request_size = Column(Integer, nullable=True, comment="请求大小（字节）")
    response_size = Column(Integer, nullable=True, comment="响应大小（字节）")
    duration_ms = Column(Integer, nullable=False, comment="请求耗时（毫秒）")
    ip_address = Column(String(50), nullable=True, comment="客户端IP地址")
    user_agent = Column(String(500), nullable=True, comment="用户代理")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间")
    
    # 索引
    __table_args__ = (
        Index('idx_audit_user_id', 'user_id'),
        Index('idx_audit_tenant_id', 'tenant_id'),
        Index('idx_audit_created_at', 'created_at'),
        Index('idx_audit_path', 'path'),
        Index('idx_audit_method', 'method'),
    )

