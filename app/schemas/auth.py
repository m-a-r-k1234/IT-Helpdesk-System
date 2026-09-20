from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    department: str | None = Field(
        default=None,
        max_length=100
    )

class LoginRequest(BaseModel):
    email: EmailStr
    password: str