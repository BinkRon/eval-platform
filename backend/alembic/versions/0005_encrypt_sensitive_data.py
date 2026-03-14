"""Encrypt existing plaintext sensitive data (api_key, auth_token).

Data-only migration — no schema changes.
Reads EVAL_ENCRYPTION_KEY from environment to encrypt existing plaintext values.

Revision ID: 0005_encrypt_sensitive_data
Revises: 0004_phase2_field_restructure
Create Date: 2026-03-14
"""

import os

import sqlalchemy as sa
from cryptography.fernet import Fernet

from alembic import op

revision = "0005_encrypt_sensitive_data"
down_revision = "0004_phase2_field_restructure"
branch_labels = None
depends_on = None


def _get_fernet() -> Fernet:
    key = os.environ.get("EVAL_ENCRYPTION_KEY", "")
    if not key:
        raise RuntimeError(
            "EVAL_ENCRYPTION_KEY must be set to run this migration. "
            "Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
        )
    return Fernet(key.encode())


def upgrade() -> None:
    fernet = _get_fernet()
    conn = op.get_bind()

    # Encrypt provider_configs.api_key
    rows = conn.execute(sa.text("SELECT id, api_key FROM provider_configs WHERE api_key IS NOT NULL AND api_key != ''"))
    for row in rows:
        encrypted = fernet.encrypt(row.api_key.encode()).decode()
        conn.execute(
            sa.text("UPDATE provider_configs SET api_key = :val WHERE id = :id"),
            {"val": encrypted, "id": row.id},
        )

    # Encrypt agent_versions.auth_token
    rows = conn.execute(sa.text("SELECT id, auth_token FROM agent_versions WHERE auth_token IS NOT NULL AND auth_token != ''"))
    for row in rows:
        encrypted = fernet.encrypt(row.auth_token.encode()).decode()
        conn.execute(
            sa.text("UPDATE agent_versions SET auth_token = :val WHERE id = :id"),
            {"val": encrypted, "id": row.id},
        )


def downgrade() -> None:
    fernet = _get_fernet()
    conn = op.get_bind()

    # Decrypt provider_configs.api_key
    rows = conn.execute(sa.text("SELECT id, api_key FROM provider_configs WHERE api_key IS NOT NULL AND api_key != ''"))
    for row in rows:
        try:
            decrypted = fernet.decrypt(row.api_key.encode()).decode()
            conn.execute(
                sa.text("UPDATE provider_configs SET api_key = :val WHERE id = :id"),
                {"val": decrypted, "id": row.id},
            )
        except Exception:
            pass  # Already plaintext

    # Decrypt agent_versions.auth_token
    rows = conn.execute(sa.text("SELECT id, auth_token FROM agent_versions WHERE auth_token IS NOT NULL AND auth_token != ''"))
    for row in rows:
        try:
            decrypted = fernet.decrypt(row.auth_token.encode()).decode()
            conn.execute(
                sa.text("UPDATE agent_versions SET auth_token = :val WHERE id = :id"),
                {"val": decrypted, "id": row.id},
            )
        except Exception:
            pass  # Already plaintext
