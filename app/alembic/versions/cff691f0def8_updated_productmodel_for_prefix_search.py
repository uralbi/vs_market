"""Updated ProductModel for prefix search

Revision ID: cff691f0def8
Revises: 8d48a587c212
Create Date: 2025-02-15 14:48:04.761470

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cff691f0def8'
down_revision: Union[str, None] = '8d48a587c212'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from alembic import op

def upgrade():
    # Ensure the `pg_trgm` extension is enabled
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # Create a GIN index with trigram search
    op.create_index(
        "idx_products_trgm",
        "products",
        ["name", "description", "category"],
        postgresql_using="gin",
        postgresql_ops={"name": "gin_trgm_ops", "description": "gin_trgm_ops", "category": "gin_trgm_ops"},
    )

def downgrade():
    # Drop the GIN index if rolling back
    op.drop_index("idx_products_trgm", table_name="products")