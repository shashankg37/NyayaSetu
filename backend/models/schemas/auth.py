from pydantic import BaseModel, EmailStr, Field

from backend.models.database import Role


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    preferred_language: str = "en"
    consent_given: bool = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class RoleUpdateRequest(BaseModel):
    role: Role


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UpdateProfileRequest(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    city: str | None = None
    issue_type: str | None = None
    preferred_language: str | None = None
    consent_given: bool | None = None


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: Role | str
    preferred_language: str
    consent_given: bool
    full_name: str | None = None
    phone: str | None = None
    city: str | None = None
    issue_type: str | None = None

    model_config = {"from_attributes": True}
