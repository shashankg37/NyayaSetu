from typing import Any

from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    id: int
    original_filename: str
    doc_type: str | None
    extracted_fields: dict[str, Any] | None
    storage_ref: str

    model_config = {"from_attributes": True}


class DraftStartRequest(BaseModel):
    doc_type: str
    known_fields: dict[str, Any] = Field(default_factory=dict)
    session_id: int | None = None


class DraftAnswerRequest(BaseModel):
    fields: dict[str, Any]


class DraftResponse(BaseModel):
    id: int
    doc_type: str
    draft_status: str
    collected_fields: dict[str, Any]
    missing_fields: list[str] = Field(default_factory=list)
    disclaimer: str = "This is an AI-generated draft for awareness purposes. It is not legally verified."
    final_file_ref: str | None = None

    model_config = {"from_attributes": True}


class ResearchRequest(BaseModel):
    query: str
    conversation_id: str | None = None


class LawyerMatchRequest(BaseModel):
    legal_domain: str | None = None
    jurisdiction: str | None = None
    state: str | None = None
    district: str | None = None
    language: str | None = None
    legal_aid_only: bool = False
    issue: str | None = None
