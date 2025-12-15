"""
租户管理测试
"""
import pytest
from fastapi import status
from app.repositories.tenant_repository import TenantRepository
from app.repositories.user_repository import UserRepository
from app.models.tenant import Tenant
from app.models.user import User
from app.core.security import password_hasher, create_access_token

@pytest.fixture
def auth_headers(client, db_session, test_tenant_data, test_user_data):
    """创建认证headers"""
    # 创建租户
    tenant_repo = TenantRepository(db_session)
    tenant = Tenant(**test_tenant_data)
    tenant = tenant_repo.create(tenant)
    
    # 创建系统管理员用户
    user_repo = UserRepository(db_session)
    user_data = {
        "username": "admin",
        "phone": "13800000000",
        "password": password_hasher.hash_password("admin123"),
        "email": "admin@example.com",
        "status": "active",
        "tenant_id": None,  # 系统管理员
        "is_system_admin": True
    }
    user = User(**user_data)
    user = user_repo.create(user)
    
    # 生成token
    token = create_access_token(data={"sub": user.id, "is_system_admin": True})
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.unit
def test_create_tenant(client, auth_headers):
    """测试创建租户"""
    response = client.post(
        "/api/v1/tenants",
        json={
            "name": "新租户",
            "code": "new_tenant",
            "status": "active"
        },
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "新租户"
    assert data["code"] == "new_tenant"

@pytest.mark.unit
def test_get_tenants(client, auth_headers, db_session, test_tenant_data):
    """测试获取租户列表"""
    # 创建测试租户
    tenant_repo = TenantRepository(db_session)
    tenant = Tenant(**test_tenant_data)
    tenant_repo.create(tenant)
    
    response = client.get("/api/v1/tenants", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

@pytest.mark.unit
def test_get_tenant_by_id(client, auth_headers, db_session, test_tenant_data):
    """测试根据ID获取租户"""
    # 创建测试租户
    tenant_repo = TenantRepository(db_session)
    tenant = Tenant(**test_tenant_data)
    tenant = tenant_repo.create(tenant)
    
    response = client.get(f"/api/v1/tenants/{tenant.id}", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == tenant.id
    assert data["name"] == test_tenant_data["name"]

@pytest.mark.unit
def test_update_tenant(client, auth_headers, db_session, test_tenant_data):
    """测试更新租户"""
    # 创建测试租户
    tenant_repo = TenantRepository(db_session)
    tenant = Tenant(**test_tenant_data)
    tenant = tenant_repo.create(tenant)
    
    response = client.put(
        f"/api/v1/tenants/{tenant.id}",
        json={
            "name": "更新后的租户",
            "code": tenant.code,
            "status": tenant.status
        },
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "更新后的租户"

@pytest.mark.unit
def test_delete_tenant(client, auth_headers, db_session, test_tenant_data):
    """测试删除租户"""
    # 创建测试租户
    tenant_repo = TenantRepository(db_session)
    tenant = Tenant(**test_tenant_data)
    tenant = tenant_repo.create(tenant)
    
    response = client.delete(f"/api/v1/tenants/{tenant.id}", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    
    # 验证已删除
    deleted_tenant = tenant_repo.get_by_id(tenant.id)
    assert deleted_tenant is None or deleted_tenant.deleted_at is not None
