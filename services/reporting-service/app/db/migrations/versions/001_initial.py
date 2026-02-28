"""Initial migration for energy_reporting_db

Revision ID: 001
Revises: 
Create Date: 2026-02-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'energy_reports',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('report_id', sa.String(36), unique=True, nullable=False),
        sa.Column('tenant_id', sa.String(50), nullable=False),
        sa.Column('report_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), server_default='pending'),
        sa.Column('params', sa.Text(), nullable=False),
        sa.Column('computation_mode', sa.String(50), nullable=True),
        sa.Column('phase_type_used', sa.String(20), nullable=True),
        sa.Column('result_json', sa.Text(), nullable=True),
        sa.Column('s3_key', sa.String(500), nullable=True),
        sa.Column('format', sa.String(10), server_default='pdf'),
        sa.Column('error_code', sa.String(100), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('progress', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_energy_reports_tenant_status', 'energy_reports', ['tenant_id', 'status'])
    op.create_index('ix_energy_reports_tenant_type_created', 'energy_reports', ['tenant_id', 'report_type', 'created_at'])

    op.create_table(
        'scheduled_reports',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('schedule_id', sa.String(36), unique=True, nullable=False),
        sa.Column('tenant_id', sa.String(50), nullable=False),
        sa.Column('report_type', sa.String(50), nullable=False),
        sa.Column('frequency', sa.String(50), nullable=False),
        sa.Column('params_template', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='1'),
        sa.Column('last_run_at', sa.DateTime(), nullable=True),
        sa.Column('next_run_at', sa.DateTime(), nullable=True),
        sa.Column('last_status', sa.String(50), nullable=True),
        sa.Column('retry_count', sa.Integer(), server_default='0'),
        sa.Column('last_result_url', sa.String(2000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    op.create_table(
        'tenant_tariffs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('tenant_id', sa.String(50), nullable=False),
        sa.Column('tariff_name', sa.String(100), nullable=False),
        sa.Column('rate_per_unit', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(10), server_default='INR'),
        sa.Column('peak_rate', sa.Float(), nullable=True),
        sa.Column('peak_start_time', sa.String(10), nullable=True),
        sa.Column('peak_end_time', sa.String(10), nullable=True),
        sa.Column('demand_charge', sa.Float(), nullable=True),
        sa.Column('power_factor_penalty', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_tenant_tariffs_tenant', 'tenant_tariffs', ['tenant_id'])


def downgrade() -> None:
    op.drop_index('idx_tenant_tariffs_tenant', 'tenant_tariffs')
    op.drop_table('tenant_tariffs')
    op.drop_table('scheduled_reports')
    op.drop_index('ix_energy_reports_tenant_type_created', 'energy_reports')
    op.drop_index('ix_energy_reports_tenant_status', 'energy_reports')
    op.drop_table('energy_reports')
