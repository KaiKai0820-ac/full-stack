"""Create UserDeviceHistory model

Revision ID: 003_create_userdevicehistory
Revises: 002_create_usersession
Create Date: 2025-01-22 00:00:02.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_create_userdevicehistory'
down_revision = '002_create_usersession'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'userdevicehistory',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('device_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('first_seen_at', sa.DateTime(), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(), nullable=False),
        sa.Column('interaction_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['userprofile.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_userdevicehistory_user_last_seen', 'userdevicehistory', ['user_id', 'last_seen_at'])


def downgrade():
    op.drop_index('ix_userdevicehistory_user_last_seen', table_name='userdevicehistory')
    op.drop_table('userdevicehistory')

