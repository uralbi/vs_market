"""added CREATOR Enum for UserModel

Revision ID: 564812197d61
Revises: 6e53b6532680
Create Date: 2025-02-28 11:52:28.733887

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '564812197d61'
down_revision: Union[str, None] = '6e53b6532680'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('orders', 'status',
               existing_type=postgresql.ENUM('PENDING', 'COMPLETED', 'FAILED', name='order_status'),
               nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('orders', 'status',
               existing_type=postgresql.ENUM('PENDING', 'COMPLETED', 'FAILED', name='order_status'),
               nullable=True)
    # ### end Alembic commands ###
