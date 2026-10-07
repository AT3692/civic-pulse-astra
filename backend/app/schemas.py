from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Category(StrEnum):
    water = "water"
    electricity = "electricity"
    sanitation = "sanitation"
    roads = "roads"
    streetlights = "streetlights"
    other = "other"


class Priority(StrEnum):
    high = "high"
    normal = "normal"
    low = "low"


class Status(StrEnum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    rejected = "rejected"


class ComplaintCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    text: str = Field(min_length=10, max_length=2000)
    location: str = Field(min_length=3, max_length=200)
    reporter_contact: str | None = Field(default=None, max_length=254)


class TriageResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category: Category
    priority: Priority
    summary: str = Field(min_length=1, max_length=140)
    confidence: float = Field(ge=0, le=1)

    @field_validator("summary")
    @classmethod
    def one_line(cls, value: str) -> str:
        if "\n" in value or "\r" in value or not value.strip():
            raise ValueError("Summary must be a nonempty single line")
        return value.strip()


class Complaint(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    text: str
    location: str
    reporter_contact: str | None
    category: Category
    priority: Priority
    status: Status
    ai_summary: str | None
    triaged_by: str
    triage_latency_ms: int
    created_at: datetime
    updated_at: datetime
    allowed_transitions: list[Status] = Field(default_factory=list)


class ComplaintPage(BaseModel):
    items: list[Complaint]
    total: int
    page: int
    page_size: int


class StatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Status


class Stats(BaseModel):
    total: int
    by_category: dict[str, int]
    by_priority: dict[str, int]
    by_status: dict[str, int]


class Outcome(BaseModel):
    provider: str
    latency_ms: int
    fallback: bool
    cache_hit: bool


class ProviderMeta(BaseModel):
    active_provider: str
    outcomes: list[Outcome]
    triage_cache_hits: int
    triage_cache_requests: int
    triage_cache_hit_rate: float


class FieldError(BaseModel):
    field: str
    message: str
    type: str


class ErrorBody(BaseModel):
    detail: str
    errors: list[FieldError] | None = None
