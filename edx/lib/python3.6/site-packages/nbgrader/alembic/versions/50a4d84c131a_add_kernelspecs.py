"""add kernelspecs

Revision ID: 50a4d84c131a
Revises: b6d005d67074
Create Date: 2017-06-01 16:48:02.243764

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '50a4d84c131a'
down_revision = 'b6d005d67074'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('notebook', sa.Column(
        'kernelspec', sa.String(1024), nullable=False,
        server_default='{}'))


def downgrade():
    op.drop_column('notebook', 'kernelspec')
