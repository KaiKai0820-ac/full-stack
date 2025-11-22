"""Create UserProfile model

Revision ID: 001_create_userprofile
Revises: 1a31ce608336
Create Date: 2025-01-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_create_userprofile'
down_revision = '1a31ce608336'
branch_labels = None
depends_on = None


def upgrade():
    # Ensure uuid-ossp extension is available
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    op.create_table(
        'userprofile',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('openid', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('nickname', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('registration_date', sa.DateTime(), nullable=False),
        sa.Column('last_active_at', sa.DateTime(), nullable=True),
        sa.Column('opt_out_flags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_userprofile_openid'), 'userprofile', ['openid'], unique=True)
    op.create_index(op.f('ix_userprofile_last_active_at'), 'userprofile', ['last_active_at'])


def downgrade():
    op.drop_index(op.f('ix_userprofile_last_active_at'), table_name='userprofile')
    op.drop_index(op.f('ix_userprofile_openid'), table_name='userprofile')
    op.drop_table('userprofile')

