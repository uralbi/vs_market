"""Updated ProductModel for full-text search

Revision ID: 587b12576926
Revises: bfd865d40efc
Create Date: 2025-02-15 14:13:11.315484

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '587b12576926'
down_revision: Union[str, None] = 'bfd865d40efc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('idx_products_exact_match', table_name='products')
    op.create_index('idx_products_exact_match', 'products', ['name', 'description', 'category', sa.text("lower('name')"), sa.text("lower('description')"), sa.text("lower('category')")], unique=False, postgresql_using='btree')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('idx_products_exact_match', table_name='products', postgresql_using='btree')
    op.create_index('idx_products_exact_match', 'products', ['name', 'description', 'category'], unique=False)
    # ### end Alembic commands ###
