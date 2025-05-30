"""added subject field to the ChatRoom Model

Revision ID: 6d5110af613f
Revises: fa26628ae7ea
Create Date: 2025-03-03 16:57:46.008771

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6d5110af613f'
down_revision: Union[str, None] = 'fa26628ae7ea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('chat_rooms', sa.Column('subject', sa.String(length=255), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('chat_rooms', 'subject')
    # ### end Alembic commands ###
