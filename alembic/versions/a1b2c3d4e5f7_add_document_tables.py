"""add document tables

Revision ID: a1b2c3d4e5f7
Revises: 01dc4a247f3
Create Date: 2025-01-15 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f7'
down_revision: Union[str, None] = '01dc4a247f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # folders 表
    op.create_table(
        'folders',
        sa.Column('id', sa.String(), nullable=False, comment='文件夹ID'),
        sa.Column('tenant_id', sa.String(), nullable=False, comment='租户ID'),
        sa.Column('user_id', sa.String(), nullable=False, comment='用户ID（拥有者）'),
        sa.Column('parent_id', sa.String(), nullable=True, comment='父文件夹ID（可为空，表示根目录）'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='文件夹名称'),
        sa.Column('path', sa.String(length=1000), nullable=False, comment='文件夹路径（租户id+用户id+文件夹层级id）'),
        sa.Column('level', sa.Integer(), nullable=False, server_default='0', comment='层级深度（0=根目录，最大2）'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='更新时间'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='软删除时间'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['parent_id'], ['folders.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_folder_tenant_user', 'folders', ['tenant_id', 'user_id'], unique=False)
    op.create_index('idx_folder_parent', 'folders', ['parent_id'], unique=False)
    op.create_index('idx_folder_deleted', 'folders', ['deleted_at'], unique=False)
    
    # documents 表
    op.create_table(
        'documents',
        sa.Column('id', sa.String(), nullable=False, comment='文档ID'),
        sa.Column('tenant_id', sa.String(), nullable=False, comment='租户ID'),
        sa.Column('user_id', sa.String(), nullable=False, comment='用户ID（拥有者）'),
        sa.Column('folder_id', sa.String(), nullable=True, comment='所属文件夹ID（可为空）'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='文件名'),
        sa.Column('original_name', sa.String(length=255), nullable=False, comment='原始文件名'),
        sa.Column('file_type', sa.String(length=20), nullable=False, comment='文件类型（txt/md/pdf/word）'),
        sa.Column('mime_type', sa.String(length=100), nullable=False, comment='MIME类型'),
        sa.Column('file_size', sa.BigInteger(), nullable=False, comment='文件大小（字节）'),
        sa.Column('file_hash', sa.String(length=64), nullable=False, comment='文件哈希值（SHA256，用于去重）'),
        sa.Column('storage_path', sa.String(length=1000), nullable=False, comment='存储路径（原文件）'),
        sa.Column('markdown_path', sa.String(length=1000), nullable=True, comment='Markdown解析结果路径'),
        sa.Column('version', sa.String(length=20), nullable=False, server_default='V1', comment='版本号（V1, V2...）'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='uploading', comment='状态：uploading/uploaded/parsing/completed/upload_failed/parse_failed'),
        sa.Column('page_count', sa.Integer(), nullable=True, comment='页数（PDF/Word）'),
        sa.Column('title', sa.String(length=500), nullable=True, comment='文档标题（解析后提取）'),
        sa.Column('summary', sa.Text(), nullable=True, comment='摘要（解析后提取）'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='更新时间'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='软删除时间'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['folder_id'], ['folders.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_document_tenant_user', 'documents', ['tenant_id', 'user_id'], unique=False)
    op.create_index('idx_document_folder', 'documents', ['folder_id'], unique=False)
    op.create_index('idx_document_status', 'documents', ['status'], unique=False)
    op.create_index('idx_document_deleted', 'documents', ['deleted_at'], unique=False)
    op.create_index('idx_document_hash', 'documents', ['file_hash'], unique=False)
    
    # document_versions 表
    op.create_table(
        'document_versions',
        sa.Column('id', sa.String(), nullable=False, comment='版本ID'),
        sa.Column('document_id', sa.String(), nullable=False, comment='文档ID'),
        sa.Column('version', sa.String(length=20), nullable=False, comment='版本号（V1, V2...）'),
        sa.Column('file_hash', sa.String(length=64), nullable=False, comment='文件哈希值'),
        sa.Column('storage_path', sa.String(length=1000), nullable=False, comment='存储路径'),
        sa.Column('markdown_path', sa.String(length=1000), nullable=True, comment='Markdown路径'),
        sa.Column('operator_id', sa.String(), nullable=False, comment='操作者ID'),
        sa.Column('remark', sa.String(length=500), nullable=True, comment='备注'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='创建时间'),
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default='0', comment='是否为当前版本'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id']),
        sa.ForeignKeyConstraint(['operator_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_version_document', 'document_versions', ['document_id'], unique=False)
    op.create_index('idx_version_current', 'document_versions', ['is_current'], unique=False)
    
    # document_tags 表
    op.create_table(
        'document_tags',
        sa.Column('id', sa.String(), nullable=False, comment='标签ID'),
        sa.Column('tenant_id', sa.String(), nullable=False, comment='租户ID'),
        sa.Column('user_id', sa.String(), nullable=False, comment='用户ID（标签属于用户）'),
        sa.Column('name', sa.String(length=20), nullable=False, comment='标签名称（20字以内）'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='创建时间'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'name', name='uq_tag_user_name')
    )
    op.create_index('idx_tag_tenant_user', 'document_tags', ['tenant_id', 'user_id'], unique=False)
    
    # document_tag_associations 表
    op.create_table(
        'document_tag_associations',
        sa.Column('id', sa.String(), nullable=False, comment='关联ID'),
        sa.Column('document_id', sa.String(), nullable=False, comment='文档ID'),
        sa.Column('tag_id', sa.String(), nullable=False, comment='标签ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='创建时间'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id']),
        sa.ForeignKeyConstraint(['tag_id'], ['document_tags.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('document_id', 'tag_id', name='uq_doc_tag')
    )
    op.create_index('idx_assoc_document', 'document_tag_associations', ['document_id'], unique=False)
    op.create_index('idx_assoc_tag', 'document_tag_associations', ['tag_id'], unique=False)
    
    # document_configs 表
    op.create_table(
        'document_configs',
        sa.Column('id', sa.String(), nullable=False, comment='配置ID'),
        sa.Column('document_id', sa.String(), nullable=False, unique=True, comment='文档ID（一对一）'),
        sa.Column('chunk_size', sa.Integer(), nullable=False, server_default='400', comment='文本切分块大小（默认400）'),
        sa.Column('chunk_overlap', sa.Integer(), nullable=False, server_default='100', comment='文本切分重叠大小（默认100）'),
        sa.Column('split_method', sa.String(length=20), nullable=False, server_default='length', comment='切分方法：length/paragraph/keyword'),
        sa.Column('split_keyword', sa.String(length=100), nullable=True, comment='切分关键字（当split_method=keyword时使用）'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='更新时间'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_config_document', 'document_configs', ['document_id'], unique=False)
    
    # user_recent_configs 表
    op.create_table(
        'user_recent_configs',
        sa.Column('id', sa.String(), nullable=False, comment='配置ID'),
        sa.Column('user_id', sa.String(), nullable=False, unique=True, comment='用户ID'),
        sa.Column('chunk_size', sa.Integer(), nullable=False, server_default='400', comment='文本切分块大小'),
        sa.Column('chunk_overlap', sa.Integer(), nullable=False, server_default='100', comment='文本切分重叠大小'),
        sa.Column('split_method', sa.String(length=20), nullable=False, server_default='length', comment='切分方法：length/paragraph/keyword'),
        sa.Column('split_keyword', sa.String(length=100), nullable=True, comment='切分关键字（当split_method=keyword时使用）'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='更新时间'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_user_recent_config')
    )
    op.create_index('idx_recent_config_user', 'user_recent_configs', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_recent_config_user', table_name='user_recent_configs')
    op.drop_table('user_recent_configs')
    
    op.drop_index('idx_config_document', table_name='document_configs')
    op.drop_table('document_configs')
    
    op.drop_index('idx_assoc_tag', table_name='document_tag_associations')
    op.drop_index('idx_assoc_document', table_name='document_tag_associations')
    op.drop_table('document_tag_associations')
    
    op.drop_index('idx_tag_tenant_user', table_name='document_tags')
    op.drop_table('document_tags')
    
    op.drop_index('idx_version_current', table_name='document_versions')
    op.drop_index('idx_version_document', table_name='document_versions')
    op.drop_table('document_versions')
    
    op.drop_index('idx_document_hash', table_name='documents')
    op.drop_index('idx_document_deleted', table_name='documents')
    op.drop_index('idx_document_status', table_name='documents')
    op.drop_index('idx_document_folder', table_name='documents')
    op.drop_index('idx_document_tenant_user', table_name='documents')
    op.drop_table('documents')
    
    op.drop_index('idx_folder_deleted', table_name='folders')
    op.drop_index('idx_folder_parent', table_name='folders')
    op.drop_index('idx_folder_tenant_user', table_name='folders')
    op.drop_table('folders')

