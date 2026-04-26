"""user resume table update

Revision ID: e957df24f435
Revises: 5dbb13e978d8
Create Date: 2026-04-25 21:43:41.191773

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e957df24f435'
down_revision: Union[str, Sequence[str], None] = '5dbb13e978d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.rename_table("candidate_resumes", "users_resumes")
    op.execute(
        "ALTER INDEX idx_candidate_resumes_owner_created "
        "RENAME TO idx_users_resumes_owner_created"
    )
    op.execute(
        "ALTER INDEX uq_candidate_resumes_owner_default "
        "RENAME TO uq_users_resumes_owner_default"
    )
    op.alter_column(
        "applications",
        "candidate_resume_id",
        new_column_name="user_resume_id",
        existing_type=sa.UUID(),
        existing_nullable=True,
    )
    op.execute(
        "ALTER INDEX idx_applications_candidate_resume "
        "RENAME TO idx_applications_user_resume"
    )
    op.execute(
        "ALTER TABLE applications RENAME CONSTRAINT "
        "fk_applications_candidate_resume_id TO fk_applications_user_resume_id"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        "ALTER TABLE applications RENAME CONSTRAINT "
        "fk_applications_user_resume_id TO fk_applications_candidate_resume_id"
    )
    op.execute(
        "ALTER INDEX idx_applications_user_resume "
        "RENAME TO idx_applications_candidate_resume"
    )
    op.alter_column(
        "applications",
        "user_resume_id",
        new_column_name="candidate_resume_id",
        existing_type=sa.UUID(),
        existing_nullable=True,
    )
    op.execute(
        "ALTER INDEX uq_users_resumes_owner_default "
        "RENAME TO uq_candidate_resumes_owner_default"
    )
    op.execute(
        "ALTER INDEX idx_users_resumes_owner_created "
        "RENAME TO idx_candidate_resumes_owner_created"
    )
    op.rename_table("users_resumes", "candidate_resumes")
