"""Create UserLocationHistory model

Revision ID: 004_create_userlocationhistory
Revises: 003_create_userdevicehistory
Create Date: 2025-01-22 00:00:03.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_create_userlocationhistory'
down_revision = '003_create_userdevicehistory'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'userlocationhistory',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ip_address', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('ip_derived_location', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('precise_location', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('location_source', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('first_seen_at', sa.DateTime(), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['userprofile.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_userlocationhistory_user_last_seen', 'userlocationhistory', ['user_id', 'last_seen_at'])
    op.create_index(op.f('ix_userlocationhistory_ip_address'), 'userlocationhistory', ['ip_address'])


def downgrade():
    op.drop_index(op.f('ix_userlocationhistory_ip_address'), table_name='userlocationhistory')
    op.drop_index('ix_userlocationhistory_user_last_seen', table_name='userlocationhistory')
    op.drop_table('userlocationhistory')

