"""Add snapshot fields to batch_tests and test_results

- batch_tests.config_snapshot (JSONB): frozen experiment config at batch creation
- test_results.sparring_prompt_snapshot (Text): actual sparring prompt sent to LLM
- test_results.judge_prompt_snapshot (Text): actual judge prompt sent to LLM

Revision ID: 0003
Revises: 0002_add_indexes
Create Date: 2026-03-08
"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0003_add_snapshot_fields"
down_revision = "0002_add_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("batch_tests", sa.Column("config_snapshot", postgresql.JSONB(), nullable=True))
    op.add_column("test_results", sa.Column("sparring_prompt_snapshot", sa.Text(), nullable=True))
    op.add_column("test_results", sa.Column("judge_prompt_snapshot", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("test_results", "judge_prompt_snapshot")
    op.drop_column("test_results", "sparring_prompt_snapshot")
    op.drop_column("batch_tests", "config_snapshot")
