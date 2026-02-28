"""Initial export_checkpoints table

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
        'export_checkpoints',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('export_id', sa.String(36), nullable=False, unique=True, index=True),
        sa.Column('device_id', sa.String(50), nullable=False, index=True),
        sa.Column('export_type', sa.String(50), nullable=False, default='full'),
        sa.Column('format', sa.String(20), nullable=False, default='csv'),
        sa.Column('start_time', sa.DateTime, nullable=False),
        sa.Column('end_time', sa.DateTime, nullable=False),
        sa.Column('status', sa.String(50), nullable=False, default='pending', index=True),
        sa.Column('records_exported', sa.Integer, default=0),
        sa.Column('s3_key', sa.String(500), nullable=True),
        sa.Column('file_size_bytes', sa.BigInteger, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('completed_at', sa.DateTime, nullable=True),
    )
    
    op.create_index('idx_export_checkpoints_device', 'export_checkpoints', ['device_id'])
    op.create_index('idx_export_checkpoints_status', 'export_checkpoints', ['status'])
    op.create_index('idx_export_checkpoints_created', 'export_checkpoints', ['created_at'])


def downgrade() -> None:
    op.drop_index('idx_export_checkpoints_created', table_name='export_checkpoints')
    op.drop_index('idx_export_checkpoints_status', table_name='export_checkpoints')
    op.drop_index('idx_export_checkpoints_device', table_name='export_checkpoints')
    op.drop_table('export_checkpoints')
