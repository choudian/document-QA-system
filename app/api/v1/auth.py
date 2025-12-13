"""
认证API
"""
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_token
from app.schemas.auth import (
    LoginRequest, TokenResponse, RegisterRequest, ResetPasswordRequest,
    ResetPasswordConfirmRequest, MFAEnableRequest, MFAVerifyRequest, MFAResponse,
    RefreshTokenRequest, RefreshTokenResponse
)
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository
from app.repositories.tenant_repository import TenantRepository
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter()
security = HTTPBearer()


def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """从 token 中获取当前用户 ID（占位实现）"""
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 token",
        )
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token 中缺少用户信息",
        )
    return user_id


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    auth_service = AuthService(
        user_repo=UserRepository(db),
        tenant_repo=TenantRepository(db),
    )
    token = auth_service.login(
        phone=payload.phone,
        credential=payload.password,
        auth_type=payload.auth_type or "password",
    )
    return TokenResponse(access_token=token, token_type="bearer")


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """
    用户注册（占位实现）
    
    注意：此功能为占位实现，实际注册功能需要根据业务需求完善
    """
    auth_service = AuthService(
        user_repo=UserRepository(db),
        tenant_repo=TenantRepository(db),
    )
    user = auth_service.register(
        tenant_id=payload.tenant_id,
        username=payload.username,
        phone=payload.phone,
        password=payload.password,
    )
    return {"message": "注册成功", "user_id": user.id}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    请求重置密码（发送验证码）（占位实现）
    
    注意：此功能为占位实现，实际实现需要集成短信/邮件服务
    """
    auth_service = AuthService(
        user_repo=UserRepository(db),
        tenant_repo=TenantRepository(db),
    )
    result = auth_service.request_password_reset(
        phone=payload.phone,
        tenant_id=payload.tenant_id,
    )
    return result


@router.post("/reset-password/confirm", status_code=status.HTTP_200_OK)
def confirm_reset_password(payload: ResetPasswordConfirmRequest, db: Session = Depends(get_db)):
    """
    确认重置密码（占位实现）
    
    注意：此功能为占位实现，实际实现需要验证验证码
    """
    auth_service = AuthService(
        user_repo=UserRepository(db),
        tenant_repo=TenantRepository(db),
    )
    result = auth_service.confirm_password_reset(
        phone=payload.phone,
        verification_code=payload.verification_code,
        new_password=payload.new_password,
        tenant_id=payload.tenant_id,
    )
    return result


@router.post("/mfa/enable", response_model=MFAResponse, status_code=status.HTTP_200_OK)
def enable_mfa(
    payload: MFAEnableRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    启用 MFA（占位实现）
    
    注意：此功能为占位实现，实际实现需要生成并存储 MFA secret
    """
    auth_service = AuthService(
        user_repo=UserRepository(db),
        tenant_repo=TenantRepository(db),
    )
    result = auth_service.enable_mfa(user_id=user_id, mfa_type=payload.mfa_type)
    return MFAResponse(**result)


@router.post("/mfa/disable", status_code=status.HTTP_200_OK)
def disable_mfa(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    禁用 MFA（占位实现）
    """
    auth_service = AuthService(
        user_repo=UserRepository(db),
        tenant_repo=TenantRepository(db),
    )
    result = auth_service.disable_mfa(user_id=user_id)
    return result


@router.post("/mfa/verify", status_code=status.HTTP_200_OK)
def verify_mfa(
    payload: MFAVerifyRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    验证 MFA 代码（占位实现）
    
    注意：此功能为占位实现，实际实现需要验证 OTP 代码
    """
    auth_service = AuthService(
        user_repo=UserRepository(db),
        tenant_repo=TenantRepository(db),
    )
    auth_service.verify_mfa(user_id=user_id, code=payload.code)
    return {"message": "MFA 验证成功"}


@router.post("/refresh", response_model=RefreshTokenResponse, status_code=status.HTTP_200_OK)
def refresh_token(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    """
    刷新访问令牌（占位实现）
    
    注意：此功能为占位实现，实际实现需要验证 refresh token 并生成新的 access token
    """
    # 占位：验证 refresh token
    payload_data = verify_token(payload.refresh_token)
    if not payload_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 refresh token",
        )
    
    user_id = payload_data.get("sub")
    tenant_id = payload_data.get("tenant_id")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="refresh token 中缺少用户信息",
        )
    
    # 占位：生成新的 access token
    from app.core.security import create_access_token
    new_access_token = create_access_token({
        "sub": user_id,
        "tenant_id": tenant_id,
    })
    
    # TODO: 实际实现应该：
    # 1. 验证 refresh token 是否有效且未过期
    # 2. 检查 refresh token 是否已被撤销
    # 3. 生成新的 access token 和 refresh token
    # 4. 可选：撤销旧的 refresh token（单次使用）
    
    return RefreshTokenResponse(
        access_token=new_access_token,
        token_type="bearer",
        refresh_token=None,  # 占位：实际应该返回新的 refresh token
    )

