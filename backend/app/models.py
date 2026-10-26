from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base

DEFAULT_GATE = {
    "runs_verified": False,
    "cicd_working": False,
    "gitops_working": None,  # None = not applicable yet (Chapters 1-3)
    "readme_published": False,
    "troubleshooting_log": False,
    "linkedin_profile": False,
    "linkedin_post": False,
    "chapter_summary": False,
}


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    chapter: Mapped[int] = mapped_column(unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    repo_url: Mapped[str | None] = mapped_column(String(500))
    post_url: Mapped[str | None] = mapped_column(String(500))
    gate: Mapped[dict] = mapped_column(JSONB, default=lambda: dict(DEFAULT_GATE))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
