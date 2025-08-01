"""Initial migration 2

Revision ID: 6cbd34fdd782
Revises: 6dce86c47c1c
Create Date: 2025-07-30 17:17:31.913321

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6cbd34fdd782'
down_revision: Union[str, Sequence[str], None] = '6dce86c47c1c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('receipt', sa.Column('is_active', sa.Boolean(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('receipt', 'is_active')
    # ### end Alembic commands ###
