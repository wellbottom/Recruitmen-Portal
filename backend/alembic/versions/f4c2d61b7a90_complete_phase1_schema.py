"""complete_phase1_schema

Revision ID: f4c2d61b7a90
Revises: e957df24f435
Create Date: 2026-04-25 22:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "f4c2d61b7a90"
down_revision: Union[str, Sequence[str], None] = "e957df24f435"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


file_purpose_enum = postgresql.ENUM(
    "profile_picture",
    "resume",
    "test_submission",
    "interview_record",
    "proctoring_media",
    name="file_purpose",
    create_type=False,
)
scan_status_enum = postgresql.ENUM(
    "pending",
    "clean",
    "infected",
    "failed",
    "skipped",
    name="scan_status",
    create_type=False,
)
profile_group_enum = postgresql.ENUM(
    "summary",
    "education",
    "experience",
    "project",
    "skill",
    "certificate",
    "award",
    "activity",
    "other",
    name="profile_group",
    create_type=False,
)
application_stage_enum = postgresql.ENUM(
    "cv_screening",
    "test",
    "interview",
    "offer",
    "final",
    "rejected",
    name="application_stage",
    create_type=False,
)


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    file_purpose_enum.create(bind, checkfirst=True)
    scan_status_enum.create(bind, checkfirst=True)
    profile_group_enum.create(bind, checkfirst=True)

    op.create_unique_constraint(
        "uq_users_resumes_id_owner",
        "users_resumes",
        ["id", "owner_user_id"],
    )
    op.create_unique_constraint(
        "uq_users_resumes_storage_location",
        "users_resumes",
        ["storage_bucket", "storage_object_path"],
    )
    op.create_check_constraint(
        "ck_users_resumes_size_non_negative",
        "users_resumes",
        "size_bytes IS NULL OR size_bytes >= 0",
    )
    op.create_check_constraint(
        "ck_users_resumes_default_requires_active",
        "users_resumes",
        "NOT is_default OR is_active",
    )
    op.drop_constraint(
        "fk_applications_user_resume_id",
        "applications",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_applications_user_resume_owner",
        "applications",
        "users_resumes",
        ["user_resume_id", "candidate_id"],
        ["id", "owner_user_id"],
    )

    op.create_table(
        "recruitment_campaigns",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=50),
            server_default=sa.text("'draft'"),
            nullable=False,
        ),
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_recruitment_campaigns_status",
        "recruitment_campaigns",
        ["status"],
        unique=False,
    )

    op.create_table(
        "positions",
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("level", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_positions_title",
        "positions",
        ["title"],
        unique=False,
    )

    op.create_table(
        "user_profile_lines",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("profile_group", profile_group_enum, nullable=False),
        sa.Column("line_content", sa.Text(), nullable=False),
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(btrim(line_content)) > 0",
            name="ck_user_profile_lines_non_empty",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_user_profile_lines_user_group",
        "user_profile_lines",
        ["user_id", "profile_group"],
        unique=False,
    )

    op.create_table(
        "file_objects",
        sa.Column("owner_user_id", sa.UUID(), nullable=False),
        sa.Column("application_id", sa.UUID(), nullable=True),
        sa.Column("purpose", file_purpose_enum, nullable=False),
        sa.Column("bucket_name", sa.String(length=100), nullable=False),
        sa.Column("object_path", sa.String(length=500), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=True),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column(
            "scan_status",
            scan_status_enum,
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column(
            "is_public",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "size_bytes IS NULL OR size_bytes >= 0",
            name="ck_file_objects_size_non_negative",
        ),
        sa.ForeignKeyConstraint(
            ["application_id"], ["applications.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "owner_user_id", name="uq_file_objects_id_owner"),
        sa.UniqueConstraint(
            "bucket_name",
            "object_path",
            name="uq_file_objects_bucket_object_path",
        ),
    )
    op.create_index(
        "idx_file_objects_owner_purpose",
        "file_objects",
        ["owner_user_id", "purpose"],
        unique=False,
    )

    op.add_column("job_posts", sa.Column("campaign_id", sa.UUID(), nullable=True))
    op.add_column("job_posts", sa.Column("position_id", sa.UUID(), nullable=True))
    op.create_index("idx_job_posts_campaign", "job_posts", ["campaign_id"], unique=False)
    op.create_index("idx_job_posts_position", "job_posts", ["position_id"], unique=False)
    op.create_foreign_key(
        "fk_job_posts_campaign_id",
        "job_posts",
        "recruitment_campaigns",
        ["campaign_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_job_posts_position_id",
        "job_posts",
        "positions",
        ["position_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.drop_constraint("job_posts_company_id_fkey", "job_posts", type_="foreignkey")
    op.drop_column("job_posts", "company_id")
    op.drop_table("companies")

    op.create_table(
        "job_requirements",
        sa.Column("job_post_id", sa.UUID(), nullable=False),
        sa.Column("requirement_type", sa.String(length=100), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "weight",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "is_mandatory",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "weight >= 0",
            name="ck_job_requirements_weight_non_negative",
        ),
        sa.ForeignKeyConstraint(["job_post_id"], ["job_posts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_job_requirements_job_post",
        "job_requirements",
        ["job_post_id"],
        unique=False,
    )

    op.create_table(
        "candidate_stage_history",
        sa.Column("application_id", sa.UUID(), nullable=False),
        sa.Column("from_stage", application_stage_enum, nullable=True),
        sa.Column("to_stage", application_stage_enum, nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("changed_by", sa.UUID(), nullable=False),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["application_id"], ["applications.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["changed_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_candidate_stage_history_application_changed",
        "candidate_stage_history",
        ["application_id", "changed_at"],
        unique=False,
    )

    op.create_table(
        "application_notes",
        sa.Column("application_id", sa.UUID(), nullable=False),
        sa.Column("author_id", sa.UUID(), nullable=False),
        sa.Column(
            "note_type",
            sa.String(length=100),
            server_default=sa.text("'general'"),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "visibility",
            sa.String(length=50),
            server_default=sa.text("'internal'"),
            nullable=False,
        ),
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["application_id"], ["applications.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_application_notes_application_created",
        "application_notes",
        ["application_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "idx_application_notes_application_created",
        table_name="application_notes",
    )
    op.drop_table("application_notes")

    op.drop_index(
        "idx_candidate_stage_history_application_changed",
        table_name="candidate_stage_history",
    )
    op.drop_table("candidate_stage_history")

    op.drop_index("idx_job_requirements_job_post", table_name="job_requirements")
    op.drop_table("job_requirements")

    op.create_table(
        "companies",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("legal_name", sa.String(length=255), nullable=True),
        sa.Column("website", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=50),
            server_default=sa.text("'active'"),
            nullable=False,
        ),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.add_column("job_posts", sa.Column("company_id", sa.UUID(), nullable=True))
    op.execute(
        """
        WITH first_user AS (
            SELECT id
            FROM users
            ORDER BY created_at NULLS LAST, id
            LIMIT 1
        ),
        inserted_company AS (
            INSERT INTO companies (name, status, created_by)
            SELECT 'Legacy Company', 'active', id
            FROM first_user
            WHERE EXISTS (SELECT 1 FROM job_posts)
            RETURNING id
        )
        UPDATE job_posts
        SET company_id = (SELECT id FROM inserted_company LIMIT 1)
        WHERE company_id IS NULL
        """
    )
    op.alter_column(
        "job_posts",
        "company_id",
        existing_type=sa.UUID(),
        nullable=False,
    )
    op.create_foreign_key(
        "job_posts_company_id_fkey",
        "job_posts",
        "companies",
        ["company_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint("fk_job_posts_position_id", "job_posts", type_="foreignkey")
    op.drop_constraint("fk_job_posts_campaign_id", "job_posts", type_="foreignkey")
    op.drop_index("idx_job_posts_position", table_name="job_posts")
    op.drop_index("idx_job_posts_campaign", table_name="job_posts")
    op.drop_column("job_posts", "position_id")
    op.drop_column("job_posts", "campaign_id")

    op.drop_index("idx_file_objects_owner_purpose", table_name="file_objects")
    op.drop_table("file_objects")

    op.drop_index(
        "idx_user_profile_lines_user_group",
        table_name="user_profile_lines",
    )
    op.drop_table("user_profile_lines")

    op.drop_index("idx_positions_title", table_name="positions")
    op.drop_table("positions")

    op.drop_index(
        "idx_recruitment_campaigns_status",
        table_name="recruitment_campaigns",
    )
    op.drop_table("recruitment_campaigns")
    op.drop_constraint(
        "fk_applications_user_resume_owner",
        "applications",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_applications_user_resume_id",
        "applications",
        "users_resumes",
        ["user_resume_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.drop_constraint(
        "ck_users_resumes_default_requires_active",
        "users_resumes",
        type_="check",
    )
    op.drop_constraint(
        "ck_users_resumes_size_non_negative",
        "users_resumes",
        type_="check",
    )
    op.drop_constraint(
        "uq_users_resumes_storage_location",
        "users_resumes",
        type_="unique",
    )
    op.drop_constraint(
        "uq_users_resumes_id_owner",
        "users_resumes",
        type_="unique",
    )

    profile_group_enum.drop(op.get_bind(), checkfirst=True)
    scan_status_enum.drop(op.get_bind(), checkfirst=True)
    file_purpose_enum.drop(op.get_bind(), checkfirst=True)
