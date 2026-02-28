"""Initial rule database schema

Revision ID: 001_initial
Revises: 
Create Date: 2026-02-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'rules',
        sa.Column('rule_id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(50), nullable=True),
        sa.Column('rule_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('scope', sa.String(50), server_default='selected_devices'),
        sa.Column('property', sa.String(100), nullable=False),
        sa.Column('condition', sa.String(20), nullable=False),
        sa.Column('threshold', sa.Float, nullable=False),
        sa.Column('status', sa.String(50), server_default='active'),
        sa.Column('severity', sa.String(20), server_default='warning'),
        sa.Column('notification_channels', sa.JSON, nullable=False),
        sa.Column('cooldown_minutes', sa.Integer, server_default='15'),
        sa.Column('device_ids', sa.JSON, nullable=False),
        sa.Column('last_triggered_at', sa.DateTime(6), nullable=True),
        sa.Column('created_at', sa.DateTime(6), nullable=False),
        sa.Column('updated_at', sa.DateTime(6), nullable=False),
        sa.Column('deleted_at', sa.DateTime(6), nullable=True),
    )
    op.create_index('idx_rules_tenant', 'rules', ['tenant_id'])
    op.create_index('idx_rules_property', 'rules', ['property'])
    op.create_index('idx_rules_status', 'rules', ['status'])

    op.create_table(
        'alerts',
        sa.Column('alert_id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(50), nullable=True),
        sa.Column('rule_id', sa.String(36), sa.ForeignKey('rules.rule_id', ondelete='CASCADE'), nullable=False),
        sa.Column('device_id', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(50), nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('actual_value', sa.Float, nullable=True),
        sa.Column('threshold_value', sa.Float, nullable=True),
        sa.Column('property_name', sa.String(100), nullable=True),
        sa.Column('condition', sa.String(20), nullable=True),
        sa.Column('status', sa.String(50), server_default='open'),
        sa.Column('acknowledged_by', sa.String(255), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(6), nullable=True),
        sa.Column('resolved_at', sa.DateTime(6), nullable=True),
        sa.Column('created_at', sa.DateTime(6), nullable=False),
        sa.Column('updated_at', sa.DateTime(6), nullable=False),
    )
    op.create_index('idx_alerts_rule', 'alerts', ['rule_id'])
    op.create_index('idx_alerts_device', 'alerts', ['device_id'])
    op.create_index('idx_alerts_status', 'alerts', ['status'])
    op.create_index('idx_alerts_created', 'alerts', ['created_at'])
    op.create_index('idx_alerts_tenant', 'alerts', ['tenant_id'])


def downgrade() -> None:
    op.drop_index('idx_alerts_tenant', 'alerts')
    op.drop_index('idx_alerts_created', 'alerts')
    op.drop_index('idx_alerts_status', 'alerts')
    op.drop_index('idx_alerts_device', 'alerts')
    op.drop_index('idx_alerts_rule', 'alerts')
    op.drop_table('alerts')

    op.drop_index('idx_rules_status', 'rules')
    op.drop_index('idx_rules_property', 'rules')
    op.drop_index('idx_rules_tenant', 'rules')
    op.drop_table('rules')
