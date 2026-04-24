from __future__ import annotations

from datetime import datetime
from enum import StrEnum
import uuid

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Index,
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
    created_companies: Mapped[list["Company"]] = relationship(
        back_populates="creator",
        foreign_keys="Company.created_by",
    )
    created_job_posts: Mapped[list["JobPost"]] = relationship(
        back_populates="creator",
        foreign_keys="JobPost.created_by",
    )
    applications: Mapped[list["Application"]] = relationship(
        back_populates="candidate",
        foreign_keys="Application.candidate_id",
    )


class Company(TimestampedUUIDMixin, Base):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    legal_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default=text("'active'"),
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    creator: Mapped["User"] = relationship(
        back_populates="created_companies",
        foreign_keys=[created_by],
    )
    job_posts: Mapped[list["JobPost"]] = relationship(back_populates="company")


class JobPost(TimestampedUUIDMixin, Base):
    __tablename__ = "job_posts"
    __table_args__ = (
        Index("idx_job_posts_status_deadline", "status", "deadline"),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
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

    company: Mapped["Company"] = relationship(back_populates="job_posts")
    creator: Mapped["User"] = relationship(
        back_populates="created_job_posts",
        foreign_keys=[created_by],
    )
    applications: Mapped[list["Application"]] = relationship(
        back_populates="job_post",
    )


class Application(TimestampedUUIDMixin, Base):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint(
            "candidate_id",
            "job_post_id",
            name="uq_applications_candidate_job_post",
        ),
        Index(
            "idx_applications_job_stage_status",
            "job_post_id",
            "current_stage",
            "status",
        ),
        Index("idx_applications_candidate", "candidate_id"),
    )

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
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
    job_post: Mapped["JobPost"] = relationship(back_populates="applications")
