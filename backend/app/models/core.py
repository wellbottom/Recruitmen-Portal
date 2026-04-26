from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
import uuid

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampedUUIDMixin


def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [member.value for member in enum_cls]


class UserStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class JobPostStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    PAUSED = "paused"
    CLOSED = "closed"
    ARCHIVED = "archived"


class ApplicationStatus(StrEnum):
    SUBMITTED = "submitted"
    SCREENING = "screening"
    TESTING = "testing"
    INTERVIEWING = "interviewing"
    OFFERED = "offered"
    HIRED = "hired"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class ApplicationStage(StrEnum):
    CV_SCREENING = "cv_screening"
    TEST = "test"
    INTERVIEW = "interview"
    OFFER = "offer"
    FINAL = "final"
    REJECTED = "rejected"


class FilePurpose(StrEnum):
    PROFILE_PICTURE = "profile_picture"
    RESUME = "resume"
    TEST_SUBMISSION = "test_submission"
    INTERVIEW_RECORD = "interview_record"
    PROCTORING_MEDIA = "proctoring_media"


class ScanStatus(StrEnum):
    PENDING = "pending"
    CLEAN = "clean"
    INFECTED = "infected"
    FAILED = "failed"
    SKIPPED = "skipped"


class ProfileGroup(StrEnum):
    SUMMARY = "summary"
    EDUCATION = "education"
    EXPERIENCE = "experience"
    PROJECT = "project"
    SKILL = "skill"
    CERTIFICATE = "certificate"
    AWARD = "award"
    ACTIVITY = "activity"
    OTHER = "other"


class UserResume(TimestampedUUIDMixin, Base):
    __tablename__ = "users_resumes"
    __table_args__ = (
        Index("idx_users_resumes_owner_created", "owner_user_id", "created_at"),
        Index(
            "uq_users_resumes_owner_default",
            "owner_user_id",
            unique=True,
            postgresql_where=text("is_default = true"),
        ),
        UniqueConstraint("id", "owner_user_id", name="uq_users_resumes_id_owner"),
        UniqueConstraint(
            "storage_bucket",
            "storage_object_path",
            name="uq_users_resumes_storage_location",
        ),
        CheckConstraint(
            "size_bytes IS NULL OR size_bytes >= 0",
            name="ck_users_resumes_size_non_negative",
        ),
        CheckConstraint(
            "NOT is_default OR is_active",
            name="ck_users_resumes_default_requires_active",
        ),
    )

    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_bucket: Mapped[str] = mapped_column(String(100), nullable=False)
    storage_object_path: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    owner: Mapped["User"] = relationship(back_populates="user_resumes")
    applications: Mapped[list["Application"]] = relationship(
        back_populates="selected_resume",
        foreign_keys="Application.user_resume_id",
    )


class Role(TimestampedUUIDMixin, Base):
    __tablename__ = "roles"
    __table_args__ = (UniqueConstraint("code", name="uq_roles_code"),)

    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    users: Mapped[list["User"]] = relationship(back_populates="role")


class User(TimestampedUUIDMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("clerk_user_id", name="uq_users_clerk_user_id"),
        UniqueConstraint("email", name="uq_users_email"),
        Index("idx_users_clerk_user_id", "clerk_user_id"),
    )

    clerk_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[UserStatus] = mapped_column(
        SqlEnum(
            UserStatus,
            name="user_status",
            values_callable=enum_values,
        ),
        nullable=False,
        server_default=text("'active'"),
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    role: Mapped["Role"] = relationship(back_populates="users")
    profile_lines: Mapped[list["UserProfileLine"]] = relationship(
        back_populates="user",
        foreign_keys="UserProfileLine.user_id",
    )
    created_job_posts: Mapped[list["JobPost"]] = relationship(
        back_populates="creator",
        foreign_keys="JobPost.created_by",
    )
    applications: Mapped[list["Application"]] = relationship(
        back_populates="candidate",
        foreign_keys="Application.candidate_id",
    )
    user_resumes: Mapped[list["UserResume"]] = relationship(
        back_populates="owner",
        foreign_keys="UserResume.owner_user_id",
    )
    file_objects: Mapped[list["FileObject"]] = relationship(
        back_populates="owner",
        foreign_keys="FileObject.owner_user_id",
    )
    stage_changes: Mapped[list["CandidateStageHistory"]] = relationship(
        back_populates="changed_by_user",
        foreign_keys="CandidateStageHistory.changed_by",
    )
    application_notes: Mapped[list["ApplicationNote"]] = relationship(
        back_populates="author",
        foreign_keys="ApplicationNote.author_id",
    )


class UserProfileLine(TimestampedUUIDMixin, Base):
    __tablename__ = "user_profile_lines"
    __table_args__ = (
        Index("idx_user_profile_lines_user_group", "user_id", "profile_group"),
        CheckConstraint(
            "length(btrim(line_content)) > 0",
            name="ck_user_profile_lines_non_empty",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    profile_group: Mapped[ProfileGroup] = mapped_column(
        SqlEnum(
            ProfileGroup,
            name="profile_group",
            values_callable=enum_values,
        ),
        nullable=False,
    )
    line_content: Mapped[str] = mapped_column(Text, nullable=False)

    user: Mapped["User"] = relationship(back_populates="profile_lines")


class FileObject(TimestampedUUIDMixin, Base):
    __tablename__ = "file_objects"
    __table_args__ = (
        UniqueConstraint(
            "bucket_name",
            "object_path",
            name="uq_file_objects_bucket_object_path",
        ),
        UniqueConstraint("id", "owner_user_id", name="uq_file_objects_id_owner"),
        Index("idx_file_objects_owner_purpose", "owner_user_id", "purpose"),
        CheckConstraint(
            "size_bytes IS NULL OR size_bytes >= 0",
            name="ck_file_objects_size_non_negative",
        ),
    )

    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    application_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="SET NULL"),
        nullable=True,
    )
    purpose: Mapped[FilePurpose] = mapped_column(
        SqlEnum(
            FilePurpose,
            name="file_purpose",
            values_callable=enum_values,
        ),
        nullable=False,
    )
    bucket_name: Mapped[str] = mapped_column(String(100), nullable=False)
    object_path: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    scan_status: Mapped[ScanStatus] = mapped_column(
        SqlEnum(
            ScanStatus,
            name="scan_status",
            values_callable=enum_values,
        ),
        nullable=False,
        server_default=text("'pending'"),
    )
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    owner: Mapped["User"] = relationship(
        back_populates="file_objects",
        foreign_keys=[owner_user_id],
    )
    application: Mapped["Application | None"] = relationship(
        back_populates="file_objects",
        foreign_keys=[application_id],
    )


class Position(TimestampedUUIDMixin, Base):
    __tablename__ = "positions"

    __table_args__ = (Index("idx_positions_title", "title"),)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    level: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    job_posts: Mapped[list["JobPost"]] = relationship(
        back_populates="position",
    )


class RecruitmentCampaign(TimestampedUUIDMixin, Base):
    __tablename__ = "recruitment_campaigns"

    __table_args__ = (Index("idx_recruitment_campaigns_status", "status"),)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default=text("'draft'"),
    )

    job_posts: Mapped[list["JobPost"]] = relationship(
        back_populates="campaign",
    )


class JobPost(TimestampedUUIDMixin, Base):
    __tablename__ = "job_posts"
    __table_args__ = (
        Index("idx_job_posts_status_deadline", "status", "deadline"),
        Index("idx_job_posts_campaign", "campaign_id"),
        Index("idx_job_posts_position", "position_id"),
    )

    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recruitment_campaigns.id", ondelete="SET NULL"),
        nullable=True,
    )
    position_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("positions.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    employment_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    status: Mapped[JobPostStatus] = mapped_column(
        SqlEnum(
            JobPostStatus,
            name="job_post_status",
            values_callable=enum_values,
        ),
        nullable=False,
        server_default=text("'draft'"),
    )
    deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    campaign: Mapped["RecruitmentCampaign | None"] = relationship(
        back_populates="job_posts",
    )
    position: Mapped["Position | None"] = relationship(
        back_populates="job_posts",
    )
    creator: Mapped["User"] = relationship(
        back_populates="created_job_posts",
        foreign_keys=[created_by],
    )
    applications: Mapped[list["Application"]] = relationship(
        back_populates="job_post",
    )
    requirements: Mapped[list["JobRequirement"]] = relationship(
        back_populates="job_post"
    )


class JobRequirement(TimestampedUUIDMixin, Base):
    __tablename__ = "job_requirements"
    __table_args__ = (
        Index("idx_job_requirements_job_post", "job_post_id"),
        CheckConstraint("weight >= 0", name="ck_job_requirements_weight_non_negative"),
    )

    job_post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("job_posts.id", ondelete="CASCADE"),
        nullable=False,
    )
    requirement_type: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    weight: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )
    is_mandatory: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    job_post: Mapped["JobPost"] = relationship(back_populates="requirements")


class Application(TimestampedUUIDMixin, Base):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint(
            "candidate_id",
            "job_post_id",
            name="uq_applications_candidate_job_post",
        ),
        ForeignKeyConstraint(
            ["user_resume_id", "candidate_id"],
            ["users_resumes.id", "users_resumes.owner_user_id"],
            name="fk_applications_user_resume_owner",
        ),
        Index(
            "idx_applications_job_stage_status",
            "job_post_id",
            "current_stage",
            "status",
        ),
        Index("idx_applications_candidate", "candidate_id"),
        Index("idx_applications_user_resume", "user_resume_id"),
    )

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_resume_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    job_post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("job_posts.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[ApplicationStatus] = mapped_column(
        SqlEnum(
            ApplicationStatus,
            name="application_status",
            values_callable=enum_values,
        ),
        nullable=False,
        server_default=text("'submitted'"),
    )
    current_stage: Mapped[ApplicationStage] = mapped_column(
        SqlEnum(
            ApplicationStage,
            name="application_stage",
            values_callable=enum_values,
        ),
        nullable=False,
        server_default=text("'cv_screening'"),
    )
    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        server_default=text("'portal'"),
    )
    applied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    final_decision_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    candidate: Mapped["User"] = relationship(
        back_populates="applications",
        foreign_keys=[candidate_id],
    )
    selected_resume: Mapped["UserResume | None"] = relationship(
        back_populates="applications",
        foreign_keys=[user_resume_id],
    )
    job_post: Mapped["JobPost"] = relationship(back_populates="applications")
    file_objects: Mapped[list["FileObject"]] = relationship(
        back_populates="application",
        foreign_keys="FileObject.application_id",
    )
    stage_history: Mapped[list["CandidateStageHistory"]] = relationship(
        back_populates="application",
        foreign_keys="CandidateStageHistory.application_id",
    )
    notes: Mapped[list["ApplicationNote"]] = relationship(
        back_populates="application",
        foreign_keys="ApplicationNote.application_id",
    )


class CandidateStageHistory(TimestampedUUIDMixin, Base):
    __tablename__ = "candidate_stage_history"
    __table_args__ = (
        Index(
            "idx_candidate_stage_history_application_changed",
            "application_id",
            "changed_at",
        ),
    )

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    from_stage: Mapped[ApplicationStage | None] = mapped_column(
        SqlEnum(
            ApplicationStage,
            name="application_stage",
            values_callable=enum_values,
            create_type=False,
        ),
        nullable=True,
    )
    to_stage: Mapped[ApplicationStage] = mapped_column(
        SqlEnum(
            ApplicationStage,
            name="application_stage",
            values_callable=enum_values,
            create_type=False,
        ),
        nullable=False,
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    application: Mapped["Application"] = relationship(
        back_populates="stage_history",
        foreign_keys=[application_id],
    )
    changed_by_user: Mapped["User"] = relationship(
        back_populates="stage_changes",
        foreign_keys=[changed_by],
    )


class ApplicationNote(TimestampedUUIDMixin, Base):
    __tablename__ = "application_notes"
    __table_args__ = (
        Index(
            "idx_application_notes_application_created",
            "application_id",
            "created_at",
        ),
    )

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    note_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        server_default=text("'general'"),
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    visibility: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default=text("'internal'"),
    )

    application: Mapped["Application"] = relationship(
        back_populates="notes",
        foreign_keys=[application_id],
    )
    author: Mapped["User"] = relationship(
        back_populates="application_notes",
        foreign_keys=[author_id],
    )
