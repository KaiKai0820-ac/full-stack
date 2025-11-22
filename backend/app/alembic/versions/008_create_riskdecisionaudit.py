"""Create RiskDecisionAudit model

Revision ID: 008_create_riskdecisionaudit
Revises: 007_create_dailycampaignmetrics
Create Date: 2025-01-22 00:00:07.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008_create_riskdecisionaudit'
down_revision = '007_create_dailycampaignmetrics'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'riskdecisionaudit',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('triggering_factors', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('mitigation_action', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('action_duration', sa.Integer(), nullable=True),
        sa.Column('decision_timestamp', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['userprofile.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('risk_score >= 0 AND risk_score <= 100', name='check_risk_score_range'),
    )
    op.create_index('ix_riskdecisionaudit_user_decision', 'riskdecisionaudit', ['user_id', 'decision_timestamp'])
    op.create_index(op.f('ix_riskdecisionaudit_decision_timestamp'), 'riskdecisionaudit', ['decision_timestamp'])


def downgrade():
    op.drop_index(op.f('ix_riskdecisionaudit_decision_timestamp'), table_name='riskdecisionaudit')
    op.drop_index('ix_riskdecisionaudit_user_decision', table_name='riskdecisionaudit')
    op.drop_table('riskdecisionaudit')

