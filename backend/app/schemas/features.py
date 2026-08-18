from pydantic import BaseModel, Field
from app.schemas.common import LegalAnswer
class QueryRequest(BaseModel): text: str = Field(min_length=2, max_length=5000); session_id: int | None = None
class KyrRequest(BaseModel): beneficiary: str = Field(min_length=2, max_length=100); topic: str = Field(min_length=2, max_length=100); situation: str | None = Field(default=None, max_length=500); session_id: int | None = None
class DocumentResponse(BaseModel): id: int; original_filename: str; doc_type: str | None; extracted_fields: dict | None
class DraftStartRequest(BaseModel): doc_type: str; known_fields: dict = Field(default_factory=dict); session_id: int | None = None
class DraftAnswerRequest(BaseModel): fields: dict
class DraftResponse(BaseModel): id: int; doc_type: str; status: str; missing_fields: list[str] = Field(default_factory=list); download_url: str | None = None
class TimelineRequest(BaseModel): narrative: str = Field(min_length=5, max_length=5000); session_id: int | None = None
class TimelineResponse(BaseModel): id: int; events: list[dict]
