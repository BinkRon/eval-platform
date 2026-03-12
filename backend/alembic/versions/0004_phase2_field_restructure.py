"""Phase 2: TestCase/EvalDimension field restructure + new tables

- TestCase: ADD sparring_prompt (migrate from persona_*) → DROP persona_background/persona_behavior
- TestCase: first_message nullable (default "喂？"), max_rounds default 50
- EvalDimension: ADD judge_prompt_segment (migrate from description + level_*_desc) → DROP old fields
- New tables: project_files, builder_conversations

Revision ID: 0004_phase2_field_restructure
Revises: 0003_add_snapshot_fields
Create Date: 2026-03-12
"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0004_phase2_field_restructure"
down_revision = "0003_add_snapshot_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # === TestCase: sparring_prompt ===
    # Step 1: Add sparring_prompt as nullable
    op.add_column("test_cases", sa.Column("sparring_prompt", sa.Text(), nullable=True))

    # Step 2: Data migration — concat persona_background + persona_behavior
    op.execute(
        sa.text("""
            UPDATE test_cases
            SET sparring_prompt = CONCAT(
                CASE WHEN persona_background IS NOT NULL AND persona_background != ''
                     THEN CONCAT('## 角色背景', E'\\n', persona_background)
                     ELSE '' END,
                CASE WHEN persona_background IS NOT NULL AND persona_background != ''
                      AND persona_behavior IS NOT NULL AND persona_behavior != ''
                     THEN E'\\n\\n' ELSE '' END,
                CASE WHEN persona_behavior IS NOT NULL AND persona_behavior != ''
                     THEN CONCAT('## 行为特征', E'\\n', persona_behavior)
                     ELSE '' END
            )
        """)
    )
    # Fill any remaining NULLs (both old fields were NULL) with a meaningful default
    op.execute(sa.text("UPDATE test_cases SET sparring_prompt = '请扮演一个普通用户进行对话。' WHERE sparring_prompt IS NULL OR sparring_prompt = ''"))

    # Step 3: Make NOT NULL
    op.alter_column("test_cases", "sparring_prompt", nullable=False)

    # Step 4: Drop old columns
    op.drop_column("test_cases", "persona_background")
    op.drop_column("test_cases", "persona_behavior")

    # === TestCase: first_message nullable, max_rounds default 50 ===
    op.alter_column("test_cases", "first_message", existing_type=sa.Text(), nullable=True)
    op.alter_column("test_cases", "max_rounds",
                    existing_type=sa.Integer(),
                    server_default=sa.text("50"))

    # === EvalDimension: judge_prompt_segment ===
    # Step 1: Add as nullable
    op.add_column("eval_dimensions", sa.Column("judge_prompt_segment", sa.Text(), nullable=True))

    # Step 2: Data migration — concat description + level_*_desc
    op.execute(
        sa.text("""
            UPDATE eval_dimensions
            SET judge_prompt_segment = CONCAT(
                COALESCE(description, ''),
                CASE WHEN description IS NOT NULL AND description != '' THEN E'\\n\\n' ELSE '' END,
                '## 评分标准', E'\\n',
                '- 3分（优秀）：', COALESCE(level_3_desc, ''), E'\\n',
                '- 2分（合格）：', COALESCE(level_2_desc, ''), E'\\n',
                '- 1分（不合格）：', COALESCE(level_1_desc, '')
            )
        """)
    )
    # Fill any remaining NULLs with a meaningful default
    op.execute(sa.text("UPDATE eval_dimensions SET judge_prompt_segment = '请评判该维度的表现。' WHERE judge_prompt_segment IS NULL OR judge_prompt_segment = ''"))

    # Step 3: Make NOT NULL
    op.alter_column("eval_dimensions", "judge_prompt_segment", nullable=False)

    # Step 4: Drop old columns
    op.drop_column("eval_dimensions", "description")
    op.drop_column("eval_dimensions", "level_3_desc")
    op.drop_column("eval_dimensions", "level_2_desc")
    op.drop_column("eval_dimensions", "level_1_desc")

    # === New table: project_files ===
    op.create_table(
        "project_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_type", sa.String(20), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_project_files_project_id", "project_files", ["project_id"])

    # === New table: builder_conversations ===
    op.create_table(
        "builder_conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("messages", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    # WARNING: This downgrade is DESTRUCTIVE.
    # sparring_prompt and judge_prompt_segment content cannot be automatically
    # restored to the old multi-column format. Persona and dimension data will be NULL after downgrade.

    # Drop new tables
    op.drop_table("builder_conversations")
    op.drop_index("ix_project_files_project_id", table_name="project_files")
    op.drop_table("project_files")

    # Restore EvalDimension old columns
    op.add_column("eval_dimensions", sa.Column("level_1_desc", sa.Text(), nullable=True))
    op.add_column("eval_dimensions", sa.Column("level_2_desc", sa.Text(), nullable=True))
    op.add_column("eval_dimensions", sa.Column("level_3_desc", sa.Text(), nullable=True))
    op.add_column("eval_dimensions", sa.Column("description", sa.Text(), nullable=True))
    op.drop_column("eval_dimensions", "judge_prompt_segment")

    # Restore TestCase
    op.alter_column("test_cases", "max_rounds",
                    existing_type=sa.Integer(),
                    server_default=None)
    op.alter_column("test_cases", "first_message", existing_type=sa.Text(), nullable=False)
    op.add_column("test_cases", sa.Column("persona_behavior", sa.Text(), nullable=True))
    op.add_column("test_cases", sa.Column("persona_background", sa.Text(), nullable=True))
    op.drop_column("test_cases", "sparring_prompt")
