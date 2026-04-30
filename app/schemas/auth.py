from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    is_active: bool
    total_consumed_tokens: int = 0


class UserUpdateRequest(BaseModel):
    email: str | None = None
    password: str | None = None
    role: str | None = None       # "user" | "admin"
    is_active: bool | None = None
