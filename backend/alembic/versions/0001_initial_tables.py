"""initial_tables

Revision ID: 0001
Revises:
Create Date: 2026-03-06 16:46:20.553863

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables with correct column types."""
    op.create_table('projects',
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('provider_configs',
    sa.Column('provider_name', sa.String(length=50), nullable=False),
    sa.Column('api_key', sa.String(length=500), nullable=True),
    sa.Column('base_url', sa.String(length=500), nullable=True),
    sa.Column('available_models', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('provider_name')
    )
    op.create_table('agent_versions',
    sa.Column('project_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('endpoint', sa.String(length=500), nullable=True),
    sa.Column('method', sa.String(length=10), nullable=False),
    sa.Column('auth_type', sa.String(length=20), nullable=True),
    sa.Column('auth_token', sa.String(length=500), nullable=True),
    sa.Column('request_template', sa.Text(), nullable=True),
    sa.Column('response_path', sa.String(length=200), nullable=True),
    sa.Column('has_end_signal', sa.Boolean(), nullable=False),
    sa.Column('end_signal_path', sa.String(length=200), nullable=True),
    sa.Column('end_signal_value', sa.String(length=100), nullable=True),
    sa.Column('connection_status', sa.String(length=20), nullable=False),
    sa.Column('response_format', sa.String(length=20), nullable=False, server_default='json'),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('judge_configs',
    sa.Column('project_id', sa.UUID(), nullable=False),
    sa.Column('pass_threshold', sa.Numeric(precision=3, scale=1), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('project_id')
    )
    op.create_table('model_configs',
    sa.Column('project_id', sa.UUID(), nullable=False),
    sa.Column('sparring_provider', sa.String(length=50), nullable=True),
    sa.Column('sparring_model', sa.String(length=100), nullable=True),
    sa.Column('sparring_temperature', sa.Numeric(), nullable=True),
    sa.Column('sparring_max_tokens', sa.Integer(), nullable=True),
    sa.Column('sparring_system_prompt', sa.Text(), nullable=True),
    sa.Column('judge_provider', sa.String(length=50), nullable=True),
    sa.Column('judge_model', sa.String(length=100), nullable=True),
    sa.Column('judge_temperature', sa.Numeric(), nullable=True),
    sa.Column('judge_max_tokens', sa.Integer(), nullable=True),
    sa.Column('judge_system_prompt', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('project_id')
    )
    op.create_table('test_cases',
    sa.Column('project_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('first_message', sa.Text(), nullable=False),
    sa.Column('persona_background', sa.Text(), nullable=True),
    sa.Column('persona_behavior', sa.Text(), nullable=True),
    sa.Column('max_rounds', sa.Integer(), nullable=False),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('batch_tests',
    sa.Column('project_id', sa.UUID(), nullable=False),
    sa.Column('agent_version_id', sa.UUID(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('concurrency', sa.Integer(), nullable=False),
    sa.Column('total_cases', sa.Integer(), nullable=False),
    sa.Column('passed_cases', sa.Integer(), nullable=False),
    sa.Column('completed_cases', sa.Integer(), nullable=False),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['agent_version_id'], ['agent_versions.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('checklist_items',
    sa.Column('judge_config_id', sa.UUID(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('level', sa.String(length=20), nullable=False),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['judge_config_id'], ['judge_configs.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('eval_dimensions',
    sa.Column('judge_config_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('level_3_desc', sa.Text(), nullable=True),
    sa.Column('level_2_desc', sa.Text(), nullable=True),
    sa.Column('level_1_desc', sa.Text(), nullable=True),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['judge_config_id'], ['judge_configs.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('test_results',
    sa.Column('batch_test_id', sa.UUID(), nullable=False),
    sa.Column('test_case_id', sa.UUID(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('conversation', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('termination_reason', sa.String(length=20), nullable=True),
    sa.Column('actual_rounds', sa.Integer(), nullable=True),
    sa.Column('checklist_results', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('eval_scores', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('judge_summary', sa.Text(), nullable=True),
    sa.Column('passed', sa.Boolean(), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['batch_test_id'], ['batch_tests.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['test_case_id'], ['test_cases.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('test_results')
    op.drop_table('eval_dimensions')
    op.drop_table('checklist_items')
    op.drop_table('batch_tests')
    op.drop_table('test_cases')
    op.drop_table('model_configs')
    op.drop_table('judge_configs')
    op.drop_table('agent_versions')
    op.drop_table('provider_configs')
    op.drop_table('projects')
