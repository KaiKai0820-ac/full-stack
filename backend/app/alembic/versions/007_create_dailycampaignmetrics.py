"""Create DailyCampaignMetrics model

Revision ID: 007_create_dailycampaignmetrics
Revises: 006_create_dailyusermetrics
Create Date: 2025-01-22 00:00:06.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007_create_dailycampaignmetrics'
down_revision = '006_create_dailyusermetrics'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'dailycampaignmetrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('campaign_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('total_impressions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_clicks', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_completions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_skips', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('ctr', sa.Float(), nullable=True),
        sa.Column('completion_rate', sa.Float(), nullable=True),
        sa.Column('skip_ratio', sa.Float(), nullable=True),
        sa.Column('computed_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('campaign_id', 'date', name='uq_dailycampaignmetrics_campaign_date'),
        sa.CheckConstraint('ctr >= 0 AND ctr <= 1', name='check_campaign_ctr_range'),
        sa.CheckConstraint('completion_rate >= 0 AND completion_rate <= 1', name='check_campaign_completion_rate_range'),
        sa.CheckConstraint('skip_ratio >= 0 AND skip_ratio <= 1', name='check_campaign_skip_ratio_range'),
    )
    op.create_index('ix_dailycampaignmetrics_campaign_date', 'dailycampaignmetrics', ['campaign_id', 'date'])
    op.create_index(op.f('ix_dailycampaignmetrics_date'), 'dailycampaignmetrics', ['date'])


def downgrade():
    op.drop_index(op.f('ix_dailycampaignmetrics_date'), table_name='dailycampaignmetrics')
    op.drop_index('ix_dailycampaignmetrics_campaign_date', table_name='dailycampaignmetrics')
    op.drop_table('dailycampaignmetrics')

