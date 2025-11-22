"""Create hourly_activity_heatmap materialized view

Revision ID: 010_create_hourly_activity_heatmap
Revises: 009_create_adinteraction_partitioned
Create Date: 2025-01-22 00:00:09.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '010_create_hourly_activity_heatmap'
down_revision = '009_create_adinteraction_partitioned'
branch_labels = None
depends_on = None


def upgrade():
    # Create materialized view for hourly activity heatmap
    op.execute("""
        CREATE MATERIALIZED VIEW hourly_activity_heatmap AS
        SELECT 
            EXTRACT(HOUR FROM timestamp)::INTEGER AS hour_of_day,
            DATE(timestamp) AS date,
            COUNT(DISTINCT user_id) AS active_user_count,
            COUNT(*) FILTER (WHERE action = 'impression') AS total_impressions,
            COUNT(*) FILTER (WHERE action = 'click') AS total_clicks,
            AVG(
                EXTRACT(EPOCH FROM (s.end_timestamp - s.start_timestamp))
            ) AS average_session_duration
        FROM ad_interaction ai
        LEFT JOIN usersession s ON ai.session_id = s.id
        WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY EXTRACT(HOUR FROM timestamp)::INTEGER, DATE(timestamp)
    """)
    
    # Create unique index on materialized view
    op.create_index(
        'ix_hourly_activity_heatmap_date_hour',
        'hourly_activity_heatmap',
        ['date', 'hour_of_day'],
        unique=True
    )


def downgrade():
    op.drop_index('ix_hourly_activity_heatmap_date_hour', table_name='hourly_activity_heatmap')
    op.execute('DROP MATERIALIZED VIEW hourly_activity_heatmap')

