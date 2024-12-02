"""Add unrelenting_standards column

Revision ID: add_unrelenting_standards
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('anxiety_logs', sa.Column('unrelenting_standards', sa.Integer(), nullable=True))

def downgrade():
    op.drop_column('anxiety_logs', 'unrelenting_standards')