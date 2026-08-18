from pydantic import BaseModel, EmailStr, Field
from app.models.models import Role
class RegisterRequest(BaseModel):
    email: EmailStr; password: str = Field(min_length=8, max_length=128); preferred_language: str = Field(default='en', max_length=32); consent_given: bool = False
class LoginRequest(BaseModel): email: EmailStr; password: str
class RefreshRequest(BaseModel): refresh_token: str
class TokenResponse(BaseModel): access_token: str; refresh_token: str; token_type: str = 'bearer'
class UserResponse(BaseModel): id: int; email: EmailStr; role: Role; preferred_language: str; consent_given: bool
class RoleUpdateRequest(BaseModel): role: Role
