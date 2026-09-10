"""Request-body schemas for write/analysis endpoints (input validation)."""
from pydantic import BaseModel, Field


class TextAnalyzeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20_000)
    case_id: str | None = Field(default=None, max_length=20)


class NetworkAnalyzeRequest(BaseModel):
    case_id: str = Field(max_length=20)


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=200)
    types: list[str] | None = None


class ReportRequest(BaseModel):
    case_id: str = Field(max_length=20)
    investigator_notes: str = Field(default="", max_length=5000)
    format: str = Field(default="json", pattern="^(json|pdf)$")


class AlertUpdateRequest(BaseModel):
    status: str | None = Field(default=None, pattern="^(NEW|UNDER_REVIEW|VERIFIED|DISMISSED)$")
    assigned_to: str | None = Field(default=None, max_length=128)
    note: str | None = Field(default=None, max_length=2000)


class AssistantQueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)


class EntityResolutionRequest(BaseModel):
    entity_type: str = Field(pattern="^(PERSON|ORGANIZATION|VEHICLE|PHONE|LOCATION|ACCOUNT)$")
