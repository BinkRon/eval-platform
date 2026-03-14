"""Add users table and project owner_id column.

- Create users table
- Insert admin seed user (password from EVAL_ADMIN_PASSWORD env var)
- Add owner_id to projects (nullable first, backfill, then NOT NULL)

Revision ID: 0006_add_users_and_project_owner
Revises: 0005_encrypt_sensitive_data
Create Date: 2026-03-14
"""

import os
import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision = "0006_add_users_and_project_owner"
down_revision = "0005_encrypt_sensitive_data"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: Create users table
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("username", sa.String(50), unique=True, nullable=False),
        sa.Column("email", sa.String(200), unique=True, nullable=True),
        sa.Column("password_hash", sa.String(200), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("role", sa.String(20), server_default="user", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Step 2: Insert admin seed user
    import bcrypt as _bcrypt

    admin_password = os.environ.get("EVAL_ADMIN_PASSWORD")
    if not admin_password:
        raise RuntimeError("EVAL_ADMIN_PASSWORD environment variable must be set for migration")
    admin_id = uuid.uuid4()
    password_hash = _bcrypt.hashpw(admin_password.encode(), _bcrypt.gensalt()).decode()

    conn = op.get_bind()
    conn.execute(
        sa.text(
            "INSERT INTO users (id, username, password_hash, role) VALUES (:id, :username, :hash, :role)"
        ),
        {"id": str(admin_id), "username": "admin", "hash": password_hash, "role": "admin"},
    )

    # Step 3: Add owner_id as nullable
    op.add_column("projects", sa.Column("owner_id", UUID(as_uuid=True), nullable=True))

    # Step 4: Backfill all existing projects with admin user
    conn.execute(
        sa.text("UPDATE projects SET owner_id = :admin_id"),
        {"admin_id": str(admin_id)},
    )

    # Step 5: Make owner_id NOT NULL + add FK
    op.alter_column("projects", "owner_id", nullable=False)
    op.create_foreign_key("fk_projects_owner_id", "projects", "users", ["owner_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_projects_owner_id", "projects", type_="foreignkey")
    op.drop_column("projects", "owner_id")
    op.drop_table("users")
