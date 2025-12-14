"""add qa tables (conversations and messages)

Revision ID: c1d2e3f4a5b6
Revises: a1b2c3d4e5f7
Create Date: 2025-01-15 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, None] = 'a1b2c3d4e5f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # conversations 表
    op.create_table(
        'conversations',
        sa.Column('id', sa.String(), nullable=False, comment='会话ID'),
        sa.Column('tenant_id', sa.String(), nullable=False, comment='租户ID'),
        sa.Column('user_id', sa.String(), nullable=False, comment='用户ID（拥有者）'),
        sa.Column('title', sa.String(length=500), nullable=True, comment='会话标题（可选，可由第一条消息自动生成）'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active', comment='状态：active/archived/deleted'),
        sa.Column('config', sa.String(length=2000), nullable=True, comment='会话配置（JSON格式）'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='更新时间'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='软删除时间'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_conversation_tenant_user', 'conversations', ['tenant_id', 'user_id'], unique=False)
    op.create_index('idx_conversation_user', 'conversations', ['user_id'], unique=False)
    op.create_index('idx_conversation_status', 'conversations', ['status'], unique=False)
    op.create_index('idx_conversation_deleted', 'conversations', ['deleted_at'], unique=False)
    
    # messages 表
    op.create_table(
        'messages',
        sa.Column('id', sa.String(), nullable=False, comment='消息ID'),
        sa.Column('conversation_id', sa.String(), nullable=False, comment='会话ID'),
        sa.Column('tenant_id', sa.String(), nullable=False, comment='租户ID'),
        sa.Column('user_id', sa.String(), nullable=False, comment='用户ID'),
        sa.Column('role', sa.String(length=20), nullable=False, comment='消息角色：user/assistant/system'),
        sa.Column('content', sa.Text(), nullable=False, comment='消息内容'),
        sa.Column('references', sa.JSON(), nullable=True, comment='引用信息（JSON格式，向量检索结果）'),
        sa.Column('prompt_tokens', sa.Integer(), nullable=True, comment='提示词Token数量'),
        sa.Column('completion_tokens', sa.Integer(), nullable=True, comment='回复Token数量'),
        sa.Column('total_tokens', sa.Integer(), nullable=True, comment='总Token数量'),
        sa.Column('metadata', sa.JSON(), nullable=True, comment='元数据（JSON格式）'),
        sa.Column('sequence', sa.Integer(), nullable=False, comment='排序序号'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='更新时间'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='软删除时间'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id']),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_message_conversation', 'messages', ['conversation_id'], unique=False)
    op.create_index('idx_message_tenant_user', 'messages', ['tenant_id', 'user_id'], unique=False)
    op.create_index('idx_message_sequence', 'messages', ['conversation_id', 'sequence'], unique=False)
    op.create_index('idx_message_deleted', 'messages', ['deleted_at'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_message_deleted', table_name='messages')
    op.drop_index('idx_message_sequence', table_name='messages')
    op.drop_index('idx_message_tenant_user', table_name='messages')
    op.drop_index('idx_message_conversation', table_name='messages')
    op.drop_table('messages')
    
    op.drop_index('idx_conversation_deleted', table_name='conversations')
    op.drop_index('idx_conversation_status', table_name='conversations')
    op.drop_index('idx_conversation_user', table_name='conversations')
    op.drop_index('idx_conversation_tenant_user', table_name='conversations')
    op.drop_table('conversations')
