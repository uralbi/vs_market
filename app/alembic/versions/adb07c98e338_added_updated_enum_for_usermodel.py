"""added updated Enum for UserModel

Revision ID: adb07c98e338
Revises: 6900aa23a1cd
Create Date: 2025-02-28 12:06:06.827638

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM

# revision identifiers, used by Alembic.
revision: str = 'adb07c98e338'
down_revision: Union[str, None] = '6900aa23a1cd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Define the new enum
new_enum = ENUM("ADMIN", "MANAGER", "USER", "CREATOR", name="userrole")
old_enum = ENUM("ADMIN", "MANAGER", "USER", name="userrole")

def upgrade():
    op.alter_column("users", "role", existing_type=old_enum, type_=new_enum, existing_nullable=False)

def downgrade():
    op.alter_column("users", "role", existing_type=new_enum, type_=old_enum, existing_nullable=False)