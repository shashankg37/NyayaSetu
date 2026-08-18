from pydantic import BaseModel, Field

class LegalAnswer(BaseModel):
    your_right: str; what_law_says: str; what_this_means: str
    what_you_can_do: list[str]; source: dict[str, str]; confidence: float = Field(ge=0, le=1); fallback_used: bool
