from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from commerce_os.shared.schemas import ReadModel


class RedditConnectorCreate(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=1, max_length=160)
    subreddit_scope: list[str] = Field(min_length=1, max_length=25)
    keyword_scope: list[str] = Field(min_length=1, max_length=100)
    time_window: Literal["hour", "day", "week", "month", "year", "all"]

    @field_validator("subreddit_scope", "keyword_scope")
    @classmethod
    def clean_scope(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values]
        if any(not value for value in cleaned):
            raise ValueError("Scope entries cannot be empty.")
        return cleaned


class RedditConnectorUpdate(BaseModel):
    status: Literal["active", "inactive", "archived"]


class RedditConnectorRead(ReadModel):
    organization_id: UUID
    connector_definition_id: UUID
    subreddit_scope: list[str]
    keyword_scope: list[str]
    time_window: str
    status: str


class RedditIngestionRequest(BaseModel):
    organization_id: UUID
    limit_per_subreddit: int = Field(default=25, ge=1, le=100)
    include_comments: bool = True
    comments_per_post: int = Field(default=10, ge=0, le=100)


class PainCandidateCreate(BaseModel):
    organization_id: UUID
    source_record_id: UUID
    pain_category: Literal["problem", "complaint", "request", "frustration", "want"]
    customer_language: str = Field(min_length=1, max_length=10_000)
    confidence_score: float = Field(ge=0, le=1)


class PainCandidateUpdate(BaseModel):
    status: Literal["reviewed", "accepted", "rejected"]


class PainCandidateRead(ReadModel):
    organization_id: UUID
    source_record_id: UUID
    pain_category: str
    customer_language: str
    confidence_score: float
    status: str


class PainEvidenceCreate(BaseModel):
    organization_id: UUID
    pain_candidate_id: UUID
    source_record_id: UUID
    evidence_strength: float = Field(ge=0, le=1)


class PainEvidenceRead(ReadModel):
    organization_id: UUID
    pain_candidate_id: UUID
    source_record_id: UUID
    evidence_strength: float


class RedditIngestionRead(BaseModel):
    job_id: UUID
    status: str
    record_count: int
    pain_candidate_count: int
