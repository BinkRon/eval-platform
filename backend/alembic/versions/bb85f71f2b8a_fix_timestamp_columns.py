"""fix_timestamp_columns

Revision ID: bb85f71f2b8a
Revises: 5e49897db95b
Create Date: 2026-03-06 18:40:57.750053

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bb85f71f2b8a'
down_revision: Union[str, Sequence[str], None] = '5e49897db95b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Tables that have created_at + updated_at (from TimestampMixin)
TABLES_WITH_TIMESTAMPS = [
    "projects",
    "provider_configs",
    "agent_versions",
    "judge_configs",
    "model_configs",
    "test_cases",
    "batch_tests",
    "test_results",
]


def upgrade() -> None:
    """Fix timestamp columns from VARCHAR to TIMESTAMP."""
    for table in TABLES_WITH_TIMESTAMPS:
        op.execute(
            f'ALTER TABLE {table} '
            f'ALTER COLUMN created_at TYPE TIMESTAMP USING created_at::timestamp, '
            f'ALTER COLUMN updated_at TYPE TIMESTAMP USING updated_at::timestamp'
        )


def downgrade() -> None:
    """Revert timestamp columns back to VARCHAR."""
    for table in TABLES_WITH_TIMESTAMPS:
        op.execute(
            f'ALTER TABLE {table} '
            f'ALTER COLUMN created_at TYPE VARCHAR USING created_at::varchar, '
            f'ALTER COLUMN updated_at TYPE VARCHAR USING updated_at::varchar'
        )
