"""add audit logs table

Revision ID: 01dc4a247f3
Revises: bd10c2d7a8a1
Create Date: 2025-01-15 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '01dc4a247f3'
down_revision: Union[str, None] = 'bd10c2d7a8a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(), nullable=False, comment='日志ID'),
        sa.Column('user_id', sa.String(), nullable=True, comment='用户ID（未登录用户为空）'),
        sa.Column('tenant_id', sa.String(), nullable=True, comment='租户ID'),
        sa.Column('method', sa.String(length=10), nullable=False, comment='HTTP方法'),
        sa.Column('path', sa.String(length=500), nullable=False, comment='请求路径'),
        sa.Column('query_params', sa.Text(), nullable=True, comment='查询参数（JSON）'),
        sa.Column('request_body', sa.Text(), nullable=True, comment='请求体（JSON，已脱敏）'),
        sa.Column('response_status', sa.Integer(), nullable=False, comment='响应状态码'),
        sa.Column('response_body', sa.Text(), nullable=True, comment='响应体（JSON，已脱敏）'),
        sa.Column('request_size', sa.Integer(), nullable=True, comment='请求大小（字节）'),
        sa.Column('response_size', sa.Integer(), nullable=True, comment='响应大小（字节）'),
        sa.Column('duration_ms', sa.Integer(), nullable=False, comment='请求耗时（毫秒）'),
        sa.Column('ip_address', sa.String(length=50), nullable=True, comment='客户端IP地址'),
        sa.Column('user_agent', sa.String(length=500), nullable=True, comment='用户代理'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='创建时间'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_audit_user_id', 'audit_logs', ['user_id'], unique=False)
    op.create_index('idx_audit_tenant_id', 'audit_logs', ['tenant_id'], unique=False)
    op.create_index('idx_audit_created_at', 'audit_logs', ['created_at'], unique=False)
    op.create_index('idx_audit_path', 'audit_logs', ['path'], unique=False)
    op.create_index('idx_audit_method', 'audit_logs', ['method'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_audit_method', table_name='audit_logs')
    op.drop_index('idx_audit_path', table_name='audit_logs')
    op.drop_index('idx_audit_created_at', table_name='audit_logs')
    op.drop_index('idx_audit_tenant_id', table_name='audit_logs')
    op.drop_index('idx_audit_user_id', table_name='audit_logs')
    op.drop_table('audit_logs')

