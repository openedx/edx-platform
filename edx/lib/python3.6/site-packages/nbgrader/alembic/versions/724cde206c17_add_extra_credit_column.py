"""add extra credit column

Revision ID: 724cde206c17
Revises: 50a4d84c131a
Create Date: 2017-06-02 13:05:22.347671

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '724cde206c17'
down_revision = '50a4d84c131a'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('grade', sa.Column('extra_credit', sa.Float(), nullable=True))


def downgrade():
    op.drop_column('grade', 'extra_credit')
