"""added products relations to UserModel

Revision ID: 349d7d66f3fb
Revises: b58b0de72b37
Create Date: 2025-02-13 15:05:57.463061

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '349d7d66f3fb'
down_revision: Union[str, None] = 'b58b0de72b37'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
