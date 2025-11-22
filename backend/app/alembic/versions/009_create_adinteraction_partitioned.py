"""Create AdInteraction table with partitioning setup

Revision ID: 009_create_adinteraction_partitioned
Revises: 008_create_riskdecisionaudit
Create Date: 2025-01-22 00:00:08.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009_create_adinteraction_partitioned'
down_revision = '008_create_riskdecisionaudit'
branch_labels = None
depends_on = None


def upgrade():
    # Create partitioned table for hot data (0-7 days)
    op.execute("""
        CREATE TABLE ad_interaction (
            interaction_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES userprofile(id),
            session_id UUID REFERENCES usersession(id),
            ad_type VARCHAR NOT NULL,
            ad_creative_id VARCHAR NOT NULL,
            placement_id VARCHAR NOT NULL,
            action VARCHAR NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            device_snapshot JSONB,
            location_snapshot JSONB,
            metadata JSONB,
            schema_version INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ) PARTITION BY RANGE (timestamp)
    """)
    
    # Create indexes on the partitioned table
    op.create_index('ix_adinteraction_user_timestamp', 'ad_interaction', ['user_id', 'timestamp'])
    op.create_index('ix_adinteraction_creative_timestamp', 'ad_interaction', ['ad_creative_id', 'timestamp'])
    op.create_index('ix_adinteraction_action_timestamp', 'ad_interaction', ['action', 'timestamp'])
    op.create_index('ix_adinteraction_timestamp', 'ad_interaction', ['timestamp'])
    op.create_index('ix_adinteraction_session_id', 'ad_interaction', ['session_id'])
    
    # Create warm table for 8-90 days data
    op.execute("""
        CREATE TABLE ad_interaction_warm (
            interaction_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES userprofile(id),
            session_id UUID REFERENCES usersession(id),
            ad_type VARCHAR NOT NULL,
            ad_creative_id VARCHAR NOT NULL,
            placement_id VARCHAR NOT NULL,
            action VARCHAR NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            device_snapshot JSONB,
            location_snapshot JSONB,
            metadata JSONB,
            schema_version INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ) PARTITION BY RANGE (timestamp)
    """)
    
    # Create indexes on warm table
    op.create_index('ix_adinteraction_warm_user_timestamp', 'ad_interaction_warm', ['user_id', 'timestamp'])
    op.create_index('ix_adinteraction_warm_creative_timestamp', 'ad_interaction_warm', ['ad_creative_id', 'timestamp'])
    op.create_index('ix_adinteraction_warm_timestamp', 'ad_interaction_warm', ['timestamp'])
    
    # Create archive table for 91-395 days data
    op.execute("""
        CREATE TABLE ad_interaction_archive (
            interaction_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES userprofile(id),
            session_id UUID REFERENCES usersession(id),
            ad_type VARCHAR NOT NULL,
            ad_creative_id VARCHAR NOT NULL,
            placement_id VARCHAR NOT NULL,
            action VARCHAR NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            device_snapshot JSONB,
            location_snapshot JSONB,
            metadata JSONB,
            schema_version INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ) PARTITION BY RANGE (timestamp)
    """)
    
    # Minimal indexes on archive table (read-only, less frequent queries)
    op.create_index('ix_adinteraction_archive_user_timestamp', 'ad_interaction_archive', ['user_id', 'timestamp'])


def downgrade():
    op.drop_index('ix_adinteraction_archive_user_timestamp', table_name='ad_interaction_archive')
    op.execute('DROP TABLE ad_interaction_archive CASCADE')
    
    op.drop_index('ix_adinteraction_warm_timestamp', table_name='ad_interaction_warm')
    op.drop_index('ix_adinteraction_warm_creative_timestamp', table_name='ad_interaction_warm')
    op.drop_index('ix_adinteraction_warm_user_timestamp', table_name='ad_interaction_warm')
    op.execute('DROP TABLE ad_interaction_warm CASCADE')
    
    op.drop_index('ix_adinteraction_session_id', table_name='ad_interaction')
    op.drop_index('ix_adinteraction_timestamp', table_name='ad_interaction')
    op.drop_index('ix_adinteraction_action_timestamp', table_name='ad_interaction')
    op.drop_index('ix_adinteraction_creative_timestamp', table_name='ad_interaction')
    op.drop_index('ix_adinteraction_user_timestamp', table_name='ad_interaction')
    op.execute('DROP TABLE ad_interaction CASCADE')

