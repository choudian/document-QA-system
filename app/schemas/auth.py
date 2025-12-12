"""
认证相关Schema
"""
from pydantic import BaseModel, Field
from typing import Optional


class LoginRequest(BaseModel):
    phone: str = Field(..., description="手机号")
    password: str = Field(..., min_length=6, max_length=72, description="密码")
    auth_type: Optional[str] = Field("password", description="认证方式，预留多种方式（如password、sso等）")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

