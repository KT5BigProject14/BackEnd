"""role update”

Revision ID: 5f1424f7be1b
Revises: 2e0b96d38d5d
Create Date: 2024-07-15 21:09:38.064004

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '5f1424f7be1b'
down_revision: Union[str, None] = '2e0b96d38d5d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_foreign_key(None, 'qna', 'users', ['email'], ['email'])
    op.drop_column('qna', 'qna_email')
    op.add_column('users', sa.Column('role', sa.String(length=50), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'role')
    op.add_column('qna', sa.Column('qna_email', mysql.VARCHAR(length=255), nullable=False))
    op.drop_constraint(None, 'qna', type_='foreignkey')
    # ### end Alembic commands ###
