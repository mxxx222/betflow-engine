"""Initial schema

Revision ID: 0001
Revises: 
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create events table
    op.create_table('events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sport', sa.String(length=50), nullable=False),
        sa.Column('league', sa.String(length=100), nullable=False),
        sa.Column('home_team', sa.String(length=200), nullable=False),
        sa.Column('away_team', sa.String(length=200), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('home_score', sa.Integer(), nullable=True),
        sa.Column('away_score', sa.Integer(), nullable=True),
        sa.Column('venue', sa.String(length=200), nullable=True),
        sa.Column('weather', sa.JSON(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_events_league'), 'events', ['league'], unique=False)
    op.create_index(op.f('ix_events_sport'), 'events', ['sport'], unique=False)
    op.create_index(op.f('ix_events_start_time'), 'events', ['start_time'], unique=False)
    op.create_index(op.f('ix_events_status'), 'events', ['status'], unique=False)

    # Create odds table
    op.create_table('odds',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('book', sa.String(length=100), nullable=False),
        sa.Column('market', sa.String(length=50), nullable=False),
        sa.Column('selection', sa.String(length=100), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('line', sa.Float(), nullable=True),
        sa.Column('implied_probability', sa.Float(), nullable=True),
        sa.Column('vig', sa.Float(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('fetched_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_odds_book'), 'odds', ['book'], unique=False)
    op.create_index(op.f('ix_odds_event_id'), 'odds', ['event_id'], unique=False)
    op.create_index(op.f('ix_odds_fetched_at'), 'odds', ['fetched_at'], unique=False)
    op.create_index(op.f('ix_odds_market'), 'odds', ['market'], unique=False)

    # Create models table
    op.create_table('models',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('version', sa.String(length=20), nullable=False),
        sa.Column('model_type', sa.String(length=50), nullable=False),
        sa.Column('parameters', sa.JSON(), nullable=True),
        sa.Column('performance_metrics', sa.JSON(), nullable=True),
        sa.Column('training_data_size', sa.Integer(), nullable=True),
        sa.Column('accuracy', sa.Float(), nullable=True),
        sa.Column('last_trained', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_models_name'), 'models', ['name'], unique=False)
    op.create_index(op.f('ix_models_status'), 'models', ['status'], unique=False)

    # Create signals table
    op.create_table('signals',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('market', sa.String(length=50), nullable=False),
        sa.Column('signal_type', sa.String(length=50), nullable=False),
        sa.Column('metrics', sa.JSON(), nullable=False),
        sa.Column('implied_probability', sa.Float(), nullable=False),
        sa.Column('fair_odds', sa.Float(), nullable=False),
        sa.Column('best_book_odds', sa.Float(), nullable=False),
        sa.Column('edge', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('risk_note', sa.Text(), nullable=True),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('model_version', sa.String(length=20), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_signals_created_at'), 'signals', ['created_at'], unique=False)
    op.create_index(op.f('ix_signals_edge'), 'signals', ['edge'], unique=False)
    op.create_index(op.f('ix_signals_event_id'), 'signals', ['event_id'], unique=False)
    op.create_index(op.f('ix_signals_expires_at'), 'signals', ['expires_at'], unique=False)
    op.create_index(op.f('ix_signals_market'), 'signals', ['market'], unique=False)
    op.create_index(op.f('ix_signals_status'), 'signals', ['status'], unique=False)

    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('actor', sa.String(length=100), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('resource', sa.String(length=100), nullable=False),
        sa.Column('resource_id', sa.String(length=100), nullable=True),
        sa.Column('diff', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_actor'), 'audit_logs', ['actor'], unique=False)
    op.create_index(op.f('ix_audit_logs_created_at'), 'audit_logs', ['created_at'], unique=False)
    op.create_index(op.f('ix_audit_logs_resource'), 'audit_logs', ['resource'], unique=False)
    op.create_index(op.f('ix_audit_logs_resource_id'), 'audit_logs', ['resource_id'], unique=False)

    # Create api_keys table
    op.create_table('api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client', sa.String(length=100), nullable=False),
        sa.Column('hash', sa.String(length=255), nullable=False),
        sa.Column('scope', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_api_keys_client'), 'api_keys', ['client'], unique=False)
    op.create_index(op.f('ix_api_keys_expires_at'), 'api_keys', ['expires_at'], unique=False)
    op.create_index(op.f('ix_api_keys_hash'), 'api_keys', ['hash'], unique=True)
    op.create_index(op.f('ix_api_keys_is_active'), 'api_keys', ['is_active'], unique=False)
    op.create_index(op.f('ix_api_keys_revoked_at'), 'api_keys', ['revoked_at'], unique=False)
    op.create_index(op.f('ix_api_keys_scope'), 'api_keys', ['scope'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_api_keys_scope'), table_name='api_keys')
    op.drop_index(op.f('ix_api_keys_revoked_at'), table_name='api_keys')
    op.drop_index(op.f('ix_api_keys_is_active'), table_name='api_keys')
    op.drop_index(op.f('ix_api_keys_hash'), table_name='api_keys')
    op.drop_index(op.f('ix_api_keys_expires_at'), table_name='api_keys')
    op.drop_index(op.f('ix_api_keys_client'), table_name='api_keys')
    op.drop_table('api_keys')
    op.drop_index(op.f('ix_audit_logs_resource_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_resource'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_created_at'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_actor'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_action'), table_name='audit_logs')
    op.drop_table('audit_logs')
    op.drop_index(op.f('ix_signals_status'), table_name='signals')
    op.drop_index(op.f('ix_signals_market'), table_name='signals')
    op.drop_index(op.f('ix_signals_expires_at'), table_name='signals')
    op.drop_index(op.f('ix_signals_event_id'), table_name='signals')
    op.drop_index(op.f('ix_signals_edge'), table_name='signals')
    op.drop_index(op.f('ix_signals_created_at'), table_name='signals')
    op.drop_table('signals')
    op.drop_index(op.f('ix_models_status'), table_name='models')
    op.drop_index(op.f('ix_models_name'), table_name='models')
    op.drop_table('models')
    op.drop_index(op.f('ix_odds_market'), table_name='odds')
    op.drop_index(op.f('ix_odds_fetched_at'), table_name='odds')
    op.drop_index(op.f('ix_odds_event_id'), table_name='odds')
    op.drop_index(op.f('ix_odds_book'), table_name='odds')
    op.drop_table('odds')
    op.drop_index(op.f('ix_events_status'), table_name='events')
    op.drop_index(op.f('ix_events_start_time'), table_name='events')
    op.drop_index(op.f('ix_events_sport'), table_name='events')
    op.drop_index(op.f('ix_events_league'), table_name='events')
    op.drop_table('events')
