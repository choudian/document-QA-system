"""
认证相关测试
"""
import pytest
from fastapi import status
from app.repositories.user_repository import UserRepository
from app.repositories.tenant_repository import TenantRepository
from app.models.user import User
from app.models.tenant import Tenant
from app.core.security import password_hasher

@pytest.mark.unit
def test_login_success(client, db_session, test_tenant_data, test_user_data):
    """测试登录成功"""
    # 创建租户
    tenant_repo = TenantRepository(db_session)
    tenant = Tenant(**test_tenant_data)
    tenant = tenant_repo.create(tenant)
    
    # 创建用户
    user_repo = UserRepository(db_session)
    user_data = test_user_data.copy()
    user_data["tenant_id"] = tenant.id
    user_data["password"] = password_hasher.hash_password(user_data["password"])
    user = User(**user_data)
    user = user_repo.create(user)
    
    # 登录
    response = client.post(
        "/api/v1/auth/login",
        json={
            "phone": test_user_data["phone"],
            "password": test_user_data["password"]
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"

@pytest.mark.unit
def test_login_invalid_credentials(client):
    """测试无效凭证登录"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "phone": "13800138000",
            "password": "wrong_password"
        }
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.unit
def test_login_missing_fields(client):
    """测试缺少字段的登录请求"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "phone": "13800138000"
        }
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
