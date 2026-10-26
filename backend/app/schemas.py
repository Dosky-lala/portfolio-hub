from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class Gate(BaseModel):
    runs_verified: bool = False
    cicd_working: bool = False
    gitops_working: bool | None = None
    readme_published: bool = False
    troubleshooting_log: bool = False
    linkedin_profile: bool = False
    linkedin_post: bool = False
    chapter_summary: bool = False


class GateUpdate(BaseModel):
    """Partial gate update: send only the boxes you want to change."""
    model_config = ConfigDict(extra="forbid")  # typo'd field names -> 422, not silently ignored

    runs_verified: bool | None = None
    cicd_working: bool | None = None
    gitops_working: bool | None = None
    readme_published: bool | None = None
    troubleshooting_log: bool | None = None
    linkedin_profile: bool | None = None
    linkedin_post: bool | None = None
    chapter_summary: bool | None = None


class ProjectCreate(BaseModel):
    chapter: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=200)
    repo_url: HttpUrl | None = None
    post_url: HttpUrl | None = None
    gate: Gate = Gate()


class ProjectUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")  # e.g. changing "chapter" is rejected

    # Typed as str (not str | None): omitting title is fine, but an explicit null -> 422
    title: str = Field(default=None, min_length=1, max_length=200)
    repo_url: HttpUrl | None = None
    post_url: HttpUrl | None = None
    gate: GateUpdate | None = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # read from SQLAlchemy objects

    id: int
    chapter: int
    title: str
    repo_url: str | None
    post_url: str | None
    gate: Gate
    created_at: datetime
    updated_at: datetime
