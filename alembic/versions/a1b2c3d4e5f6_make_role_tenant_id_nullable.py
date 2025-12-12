"""make_role_tenant_id_nullable

Revision ID: a1b2c3d4e5f6
Revises: 1b139939a729
Create Date: 2025-12-12 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '1b139939a729'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 修改 roles 表的 tenant_id 字段，允许 NULL 值（系统级角色）
    # SQLite 的 batch_alter_table 会自动处理外键约束
    with op.batch_alter_table('roles', schema=None) as batch_op:
        batch_op.alter_column(
            'tenant_id',
            existing_type=sa.String(),
            nullable=True,
            existing_nullable=False,
            comment='租户ID，None表示系统级角色（如租户管理员）',
        )


def downgrade() -> None:
    # 恢复 roles 表的 tenant_id 字段为 NOT NULL
    # 注意：如果数据库中已有 tenant_id 为 NULL 的记录，需要先删除或更新这些记录
    with op.batch_alter_table('roles', schema=None) as batch_op:
        batch_op.alter_column(
            'tenant_id',
            existing_type=sa.String(),
            nullable=False,
            existing_nullable=True,
            comment='租户ID',
        )
