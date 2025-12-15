"""
用户管理测试
"""
import pytest
from fastapi import status
from app.repositories.user_repository import UserRepository
from app.repositories.tenant_repository import TenantRepository
from app.models.user import User
from app.models.tenant import Tenant
from app.core.security import password_hasher, create_access_token

@pytest.fixture
def tenant_user_headers(client, db_session, test_tenant_data):
    """创建租户管理员认证headers"""
    # 创建租户
    tenant_repo = TenantRepository(db_session)
    tenant = Tenant(**test_tenant_data)
    tenant = tenant_repo.create(tenant)
    
    # 创建租户管理员用户
    user_repo = UserRepository(db_session)
    user_data = {
        "username": "tenant_admin",
        "phone": "13900000000",
        "password": get_password_hash("admin123"),
        "email": "admin@tenant.com",
        "status": "active",
        "tenant_id": tenant.id,
        "is_system_admin": False
    }
    user = User(**user_data)
    user = user_repo.create(user)
    
    # 生成token
    token = create_access_token(data={"sub": user.id, "tenant_id": tenant.id})
    return {"Authorization": f"Bearer {token}"}, tenant

@pytest.mark.unit
def test_create_user(client, tenant_user_headers):
    """测试创建用户"""
    headers, tenant = tenant_user_headers
    
    response = client.post(
        "/api/v1/users",
        json={
            "username": "newuser",
            "phone": "13700000000",
            "password": "password123",
            "email": "newuser@example.com",
            "tenant_id": tenant.id,
            "status": "active"
        },
        headers=headers
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["username"] == "newuser"
    assert data["phone"] == "13700000000"

@pytest.mark.unit
def test_get_users(client, tenant_user_headers, db_session, test_user_data):
    """测试获取用户列表"""
    headers, tenant = tenant_user_headers
    
    # 创建测试用户
    user_repo = UserRepository(db_session)
    user_data = test_user_data.copy()
    user_data["tenant_id"] = tenant.id
    user_data["password"] = password_hasher.hash_password(user_data["password"])
    user = User(**user_data)
    user_repo.create(user)
    
    response = client.get(
        f"/api/v1/users?tenant_id={tenant.id}",
        headers=headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)

@pytest.mark.unit
def test_get_user_by_id(client, tenant_user_headers, db_session, test_user_data):
    """测试根据ID获取用户"""
    headers, tenant = tenant_user_headers
    
    # 创建测试用户
    user_repo = UserRepository(db_session)
    user_data = test_user_data.copy()
    user_data["tenant_id"] = tenant.id
    user_data["password"] = password_hasher.hash_password(user_data["password"])
    user = User(**user_data)
    user = user_repo.create(user)
    
    response = client.get(f"/api/v1/users/{user.id}", headers=headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == user.id
    assert data["username"] == test_user_data["username"]

@pytest.mark.unit
def test_update_user(client, tenant_user_headers, db_session, test_user_data):
    """测试更新用户"""
    headers, tenant = tenant_user_headers
    
    # 创建测试用户
    user_repo = UserRepository(db_session)
    user_data = test_user_data.copy()
    user_data["tenant_id"] = tenant.id
    user_data["password"] = password_hasher.hash_password(user_data["password"])
    user = User(**user_data)
    user = user_repo.create(user)
    
    response = client.put(
        f"/api/v1/users/{user.id}",
        json={
            "username": "updated_user",
            "phone": user.phone,
            "email": "updated@example.com",
            "tenant_id": tenant.id,
            "status": user.status
        },
        headers=headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == "updated_user"
