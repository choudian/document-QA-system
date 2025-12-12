"""add_system_admin_support

Revision ID: f6709dc3d64d
Revises: 260b8efc4504
Create Date: 2025-12-11 17:09:22.903425

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6709dc3d64d'
down_revision: Union[str, None] = '260b8efc4504'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column(
            'tenant_id',
            existing_type=sa.String(),
            nullable=True,
            existing_nullable=True,
            comment="租户ID（系统管理员为空）",
        )
        batch_op.add_column(sa.Column('is_system_admin', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.create_unique_constraint('uq_user_phone_global', ['phone'])


def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint('uq_user_phone_global', type_='unique')
        batch_op.drop_column('is_system_admin')
        batch_op.alter_column(
            'tenant_id',
            existing_type=sa.String(),
            nullable=False,
            existing_nullable=True,
            comment="租户ID",
        )

