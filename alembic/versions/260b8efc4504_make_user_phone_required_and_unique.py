"""make_user_phone_required_and_unique

Revision ID: 260b8efc4504
Revises: 95455ceddada
Create Date: 2025-12-11 16:47:18.033904

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '260b8efc4504'
down_revision: Union[str, None] = '95455ceddada'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        # 设置手机号非空
        batch_op.alter_column(
            'phone',
            existing_type=sa.String(length=20),
            nullable=False,
            existing_nullable=True,
            comment="手机号"
        )
        # 添加租户内手机号唯一约束
        batch_op.create_unique_constraint('uq_tenant_phone', ['tenant_id', 'phone'])


def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint('uq_tenant_phone', type_='unique')
        batch_op.alter_column(
            'phone',
            existing_type=sa.String(length=20),
            nullable=True,
            existing_nullable=False,
            comment="手机号"
        )

