"""Initial migration

Revision ID: 355ac71de9bb
Revises: 
Create Date: 2025-02-24 21:02:23.133654

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '355ac71de9bb'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from sqlalchemy.sql import text

def upgrade() -> None:
    # Ensure the ENUM type is created correctly
    op.execute("""
        DO $$ 
        BEGIN 
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'userrole') THEN 
                CREATE TYPE userrole AS ENUM ('admin', 'manager', 'user'); 
            END IF; 
        END $$ LANGUAGE plpgsql;
    """)

    # ✅ Ensure the column name remains 'role'
    op.add_column('users', sa.Column(
        'role',  # ✅ Keep correct column name
        sa.Enum('admin', 'manager', 'user', name='userrole'), 
        server_default='user',  # ✅ Lowercase ENUM value
        nullable=False
    ))

def downgrade() -> None:
    # Remove the column
    op.drop_column('users', 'role')
    # Drop the ENUM type
    op.execute("DROP TYPE IF EXISTS userrole CASCADE;")
