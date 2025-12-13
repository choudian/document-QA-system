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


class RegisterRequest(BaseModel):
    """注册请求"""
    tenant_id: str = Field(..., description="租户ID")
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    phone: str = Field(..., description="手机号")
    password: str = Field(..., min_length=6, max_length=72, description="密码")


class ResetPasswordRequest(BaseModel):
    """重置密码请求（发送验证码）"""
    phone: str = Field(..., description="手机号")
    tenant_id: Optional[str] = Field(None, description="租户ID（可选）")


class ResetPasswordConfirmRequest(BaseModel):
    """确认重置密码请求"""
    phone: str = Field(..., description="手机号")
    verification_code: str = Field(..., description="验证码")
    new_password: str = Field(..., min_length=6, max_length=72, description="新密码")
    tenant_id: Optional[str] = Field(None, description="租户ID（可选）")


class MFAEnableRequest(BaseModel):
    """启用 MFA 请求"""
    mfa_type: str = Field("otp", description="MFA 类型：otp/sms/email")


class MFAVerifyRequest(BaseModel):
    """验证 MFA 请求"""
    code: str = Field(..., description="MFA 验证码")


class MFAResponse(BaseModel):
    """MFA 响应"""
    enabled: bool
    secret: Optional[str] = None  # 仅首次启用时返回，用于显示二维码
    qr_code_url: Optional[str] = None  # 二维码 URL（如果支持）


class RefreshTokenRequest(BaseModel):
    """刷新 Token 请求"""
    refresh_token: str = Field(..., description="刷新 Token")


class RefreshTokenResponse(BaseModel):
    """刷新 Token 响应"""
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None  # 新的刷新 Token（如果支持刷新）