"""Initial analytics_jobs table

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
        'analytics_jobs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('job_id', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('device_id', sa.String(50), nullable=False, index=True),
        sa.Column('analysis_type', sa.String(50), nullable=False),
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('date_range_start', sa.DateTime, nullable=False),
        sa.Column('date_range_end', sa.DateTime, nullable=False),
        sa.Column('parameters', sa.JSON, nullable=True),
        sa.Column('status', sa.String(50), nullable=False, default='pending', index=True),
        sa.Column('progress', sa.Float, nullable=True),
        sa.Column('message', sa.Text, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('results', sa.JSON, nullable=True),
        sa.Column('accuracy_metrics', sa.JSON, nullable=True),
        sa.Column('execution_time_seconds', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('started_at', sa.DateTime, nullable=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )
    
    op.create_index('idx_analytics_jobs_status', 'analytics_jobs', ['status'])
    op.create_index('idx_analytics_jobs_created', 'analytics_jobs', ['created_at'])
    op.create_index('idx_analytics_jobs_device', 'analytics_jobs', ['device_id'])


def downgrade() -> None:
    op.drop_index('idx_analytics_jobs_device', table_name='analytics_jobs')
    op.drop_index('idx_analytics_jobs_created', table_name='analytics_jobs')
    op.drop_index('idx_analytics_jobs_status', table_name='analytics_jobs')
    op.drop_table('analytics_jobs')
