"""Add indexes for high-frequency query fields

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-06
"""
from alembic import op

revision = "0002_add_indexes"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_agent_versions_project_id", "agent_versions", ["project_id"])
    op.create_index("ix_test_cases_project_id", "test_cases", ["project_id"])
    op.create_index("ix_batch_tests_project_id", "batch_tests", ["project_id"])
    op.create_index("ix_batch_tests_status", "batch_tests", ["status"])
    op.create_index("ix_test_results_batch_test_id", "test_results", ["batch_test_id"])
    op.create_index("ix_test_results_status", "test_results", ["status"])


def downgrade() -> None:
    op.drop_index("ix_test_results_status", table_name="test_results")
    op.drop_index("ix_test_results_batch_test_id", table_name="test_results")
    op.drop_index("ix_batch_tests_status", table_name="batch_tests")
    op.drop_index("ix_batch_tests_project_id", table_name="batch_tests")
    op.drop_index("ix_test_cases_project_id", table_name="test_cases")
    op.drop_index("ix_agent_versions_project_id", table_name="agent_versions")
