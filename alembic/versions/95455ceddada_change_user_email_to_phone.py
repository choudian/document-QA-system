"""change_user_email_to_phone

Revision ID: 95455ceddada
Revises: e17f03d0744c
Create Date: 2025-12-11 16:37:36.122389

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '95455ceddada'
down_revision: Union[str, None] = 'e17f03d0744c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLite 需要使用 batch 模式来修改列
    with op.batch_alter_table('users', schema=None) as batch_op:
        # 重命名列：email -> phone
        batch_op.alter_column('email',
                              new_column_name='phone',
                              type_=sa.String(length=20),
                              existing_type=sa.String(length=100),
                              existing_nullable=True,
                              comment='手机号')
    # 对于非SQLite数据库，可以直接使用：
    # op.alter_column('users', 'email',
    #                  new_column_name='phone',
    #                  type_=sa.String(length=20),
    #                  existing_type=sa.String(length=100),
    #                  existing_nullable=True,
    #                  comment='手机号')


def downgrade() -> None:
    # SQLite 需要使用 batch 模式来修改列
    with op.batch_alter_table('users', schema=None) as batch_op:
        # 重命名列：phone -> email
        batch_op.alter_column('phone',
                              new_column_name='email',
                              type_=sa.String(length=100),
                              existing_type=sa.String(length=20),
                              existing_nullable=True,
                              comment='邮箱')
    # 对于非SQLite数据库，可以直接使用：
    # op.alter_column('users', 'phone',
    #                  new_column_name='email',
    #                  type_=sa.String(length=100),
    #                  existing_type=sa.String(length=20),
    #                  existing_nullable=True,
    #                  comment='邮箱')

