"""added price field MovieModel

Revision ID: 96f515196174
Revises: 1ce075ffdd7f
Create Date: 2025-02-27 12:26:53.831204

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '96f515196174'
down_revision: Union[str, None] = '1ce075ffdd7f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('movies', sa.Column('price', sa.Float(), nullable=True))
    op.execute("UPDATE movies SET price = 100")
    op.alter_column('movies', 'price', nullable=False)
    op.drop_column('users', 'role_temp')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('role_temp', sa.TEXT(), autoincrement=False, nullable=True))
    op.drop_column('movies', 'price')
    # ### end Alembic commands ###
