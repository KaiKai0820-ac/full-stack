"""Create UserSession model

Revision ID: 002_create_usersession
Revises: 001_create_userprofile
Create Date: 2025-01-22 00:00:01.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_create_usersession'
down_revision = '001_create_userprofile'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'usersession',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('start_timestamp', sa.DateTime(), nullable=False),
        sa.Column('end_timestamp', sa.DateTime(), nullable=True),
        sa.Column('duration', sa.Integer(), nullable=True),
        sa.Column('ip_address', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('device_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('location_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['userprofile.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_usersession_user_id'), 'usersession', ['user_id'])
    op.create_index(op.f('ix_usersession_start_timestamp'), 'usersession', ['start_timestamp'])
    op.create_index('ix_usersession_user_start', 'usersession', ['user_id', 'start_timestamp'])


def downgrade():
    op.drop_index('ix_usersession_user_start', table_name='usersession')
    op.drop_index(op.f('ix_usersession_start_timestamp'), table_name='usersession')
    op.drop_index(op.f('ix_usersession_user_id'), table_name='usersession')
    op.drop_table('usersession')

