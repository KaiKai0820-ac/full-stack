"""Create UserActivityPattern model

Revision ID: 005_create_useractivitypattern
Revises: 004_create_userlocationhistory
Create Date: 2025-01-22 00:00:04.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005_create_useractivitypattern'
down_revision = '004_create_userlocationhistory'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'useractivitypattern',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('hour_of_day', sa.Integer(), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('average_session_start_time', sa.Time(), nullable=True),
        sa.Column('average_session_duration', sa.Integer(), nullable=True),
        sa.Column('total_sessions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('most_active_periods', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('computed_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['userprofile.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('hour_of_day >= 0 AND hour_of_day <= 23', name='check_hour_of_day'),
        sa.CheckConstraint('day_of_week >= 0 AND day_of_week <= 6', name='check_day_of_week'),
    )
    op.create_index('ix_useractivitypattern_user_hour_day', 'useractivitypattern', ['user_id', 'hour_of_day', 'day_of_week'])
    op.create_index('ix_useractivitypattern_hour_day', 'useractivitypattern', ['hour_of_day', 'day_of_week'])


def downgrade():
    op.drop_index('ix_useractivitypattern_hour_day', table_name='useractivitypattern')
    op.drop_index('ix_useractivitypattern_user_hour_day', table_name='useractivitypattern')
    op.drop_table('useractivitypattern')

