"""add config tables

Revision ID: bd10c2d7a8a1
Revises: f6709dc3d64d
Create Date: 2025-01-15 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bd10c2d7a8a1'
down_revision: Union[str, None] = 'f6709dc3d64d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # system_configs
    op.create_table(
        'system_configs',
        sa.Column('id', sa.String(), nullable=False, comment='配置ID'),
        sa.Column('tenant_id', sa.String(), nullable=True, comment='租户ID，空表示系统级'),
        sa.Column('category', sa.String(length=50), nullable=False, comment='配置类别'),
        sa.Column('key', sa.String(length=100), nullable=False, comment='配置键'),
        sa.Column('value', sa.Text(), nullable=False, comment='配置值(JSON字符串)'),
        sa.Column('status', sa.Boolean(), nullable=False, server_default='1', comment='启用状态'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='更新时间'),
        sa.Column('created_by', sa.String(), nullable=True, comment='创建人ID'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'category', 'key', name='uq_system_config_scope_key')
    )
    op.create_index('idx_system_config_tenant', 'system_configs', ['tenant_id'], unique=False)
    op.create_index('idx_system_config_category_key', 'system_configs', ['category', 'key'], unique=False)

    # user_configs
    op.create_table(
        'user_configs',
        sa.Column('id', sa.String(), nullable=False, comment='配置ID'),
        sa.Column('user_id', sa.String(), nullable=False, comment='用户ID'),
        sa.Column('category', sa.String(length=50), nullable=False, comment='配置类别'),
        sa.Column('key', sa.String(length=100), nullable=False, comment='配置键'),
        sa.Column('value', sa.Text(), nullable=False, comment='配置值(JSON字符串)'),
        sa.Column('status', sa.Boolean(), nullable=False, server_default='1', comment='启用状态'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='更新时间'),
        sa.Column('created_by', sa.String(), nullable=True, comment='创建人ID'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'category', 'key', name='uq_user_config_scope_key')
    )
    op.create_index('idx_user_config_user', 'user_configs', ['user_id'], unique=False)
    op.create_index('idx_user_config_category_key', 'user_configs', ['category', 'key'], unique=False)

    # config_histories
    op.create_table(
        'config_histories',
        sa.Column('id', sa.String(), nullable=False, comment='记录ID'),
        sa.Column('scope_type', sa.String(length=10), nullable=False, comment='作用域类型：system/tenant/user'),
        sa.Column('scope_id', sa.String(), nullable=True, comment='作用域ID'),
        sa.Column('category', sa.String(length=50), nullable=False, comment='配置类别'),
        sa.Column('key', sa.String(length=100), nullable=False, comment='配置键'),
        sa.Column('old_value', sa.Text(), nullable=True, comment='旧值(JSON字符串)'),
        sa.Column('new_value', sa.Text(), nullable=True, comment='新值(JSON字符串)'),
        sa.Column('operator_id', sa.String(), nullable=True, comment='操作人ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='创建时间'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_config_history_scope', 'config_histories', ['scope_type', 'scope_id'], unique=False)
    op.create_index('idx_config_history_category_key', 'config_histories', ['category', 'key'], unique=False)
    op.create_index('idx_config_history_created', 'config_histories', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_config_history_created', table_name='config_histories')
    op.drop_index('idx_config_history_category_key', table_name='config_histories')
    op.drop_index('idx_config_history_scope', table_name='config_histories')
    op.drop_table('config_histories')

    op.drop_index('idx_user_config_category_key', table_name='user_configs')
    op.drop_index('idx_user_config_user', table_name='user_configs')
    op.drop_table('user_configs')

    op.drop_index('idx_system_config_category_key', table_name='system_configs')
    op.drop_index('idx_system_config_tenant', table_name='system_configs')
    op.drop_table('system_configs')

