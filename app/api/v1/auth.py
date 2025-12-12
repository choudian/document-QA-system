"""
认证API
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository
from app.repositories.tenant_repository import TenantRepository

router = APIRouter()


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

