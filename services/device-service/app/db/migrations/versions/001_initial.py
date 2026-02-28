"""Initial device database schema

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
        'devices',
        sa.Column('device_id', sa.String(50), primary_key=True),
        sa.Column('tenant_id', sa.String(50), nullable=True),
        sa.Column('device_name', sa.String(255), nullable=False),
        sa.Column('device_type', sa.String(100), nullable=False),
        sa.Column('manufacturer', sa.String(255), nullable=True),
        sa.Column('model', sa.String(255), nullable=True),
        sa.Column('location', sa.String(500), nullable=True),
        sa.Column('phase_type', sa.String(20), nullable=True),
        sa.Column('legacy_status', sa.String(50), server_default='active'),
        sa.Column('last_seen_timestamp', sa.DateTime(6), nullable=True),
        sa.Column('metadata_json', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(6), nullable=False),
        sa.Column('updated_at', sa.DateTime(6), nullable=False),
        sa.Column('deleted_at', sa.DateTime(6), nullable=True),
    )
    op.create_index('idx_tenant', 'devices', ['tenant_id'])
    op.create_index('idx_device_type', 'devices', ['device_type'])
    op.create_index('idx_last_seen', 'devices', ['last_seen_timestamp'])
    op.create_index('idx_legacy_status', 'devices', ['legacy_status'])
    
    op.create_table(
        'device_shifts',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('device_id', sa.String(50), sa.ForeignKey('devices.device_id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id', sa.String(50), nullable=True),
        sa.Column('shift_name', sa.String(100), nullable=False),
        sa.Column('shift_start', sa.Time, nullable=False),
        sa.Column('shift_end', sa.Time, nullable=False),
        sa.Column('maintenance_break_minutes', sa.Integer, server_default='0'),
        sa.Column('day_of_week', sa.Integer, nullable=True),
        sa.Column('is_active', sa.Boolean, server_default='1'),
        sa.Column('created_at', sa.DateTime(6), nullable=False),
        sa.Column('updated_at', sa.DateTime(6), nullable=False),
    )
    op.create_index('idx_device_shifts_device', 'device_shifts', ['device_id'])
    op.create_index('idx_device_shifts_tenant', 'device_shifts', ['tenant_id'])
    
    op.create_table(
        'parameter_health_config',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('device_id', sa.String(50), sa.ForeignKey('devices.device_id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id', sa.String(50), nullable=True),
        sa.Column('parameter_name', sa.String(100), nullable=False),
        sa.Column('normal_min', sa.Float, nullable=True),
        sa.Column('normal_max', sa.Float, nullable=True),
        sa.Column('max_min', sa.Float, nullable=True),
        sa.Column('max_max', sa.Float, nullable=True),
        sa.Column('weight', sa.Float, server_default='0.0'),
        sa.Column('ignore_zero_value', sa.Boolean, server_default='0'),
        sa.Column('is_active', sa.Boolean, server_default='1'),
        sa.Column('created_at', sa.DateTime(6), nullable=False),
        sa.Column('updated_at', sa.DateTime(6), nullable=False),
    )
    op.create_index('idx_health_config_device', 'parameter_health_config', ['device_id'])
    op.create_index('idx_health_config_tenant', 'parameter_health_config', ['tenant_id'])
    op.create_unique_constraint('uk_device_parameter', 'parameter_health_config', ['device_id', 'parameter_name'])
    
    op.create_table(
        'device_properties',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('device_id', sa.String(50), sa.ForeignKey('devices.device_id', ondelete='CASCADE'), nullable=False),
        sa.Column('property_name', sa.String(100), nullable=False),
        sa.Column('data_type', sa.String(20), server_default='float'),
        sa.Column('is_numeric', sa.Boolean, server_default='1'),
        sa.Column('discovered_at', sa.DateTime(6), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(6), nullable=False),
    )
    op.create_index('idx_device_properties_device', 'device_properties', ['device_id'])
    op.create_unique_constraint('uk_device_property', 'device_properties', ['device_id', 'property_name'])


def downgrade() -> None:
    op.drop_table('device_properties')
    op.drop_table('parameter_health_config')
    op.drop_table('device_shifts')
    op.drop_table('devices')
