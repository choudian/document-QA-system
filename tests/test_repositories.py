"""
Repository层测试
"""
import pytest
from app.repositories.tenant_repository import TenantRepository
from app.repositories.user_repository import UserRepository
from app.models.tenant import Tenant
from app.models.user import User
from app.core.security import password_hasher

@pytest.mark.unit
def test_tenant_repository_create(db_session, test_tenant_data):
    """测试租户Repository创建"""
    repo = TenantRepository(db_session)
    tenant = Tenant(**test_tenant_data)
    created_tenant = repo.create(tenant)
    
    assert created_tenant.id is not None
    assert created_tenant.name == test_tenant_data["name"]
    assert created_tenant.code == test_tenant_data["code"]

@pytest.mark.unit
def test_tenant_repository_get_by_id(db_session, test_tenant_data):
    """测试租户Repository根据ID查询"""
    repo = TenantRepository(db_session)
    tenant = Tenant(**test_tenant_data)
    created_tenant = repo.create(tenant)
    
    found_tenant = repo.get_by_id(created_tenant.id)
    
    assert found_tenant is not None
    assert found_tenant.id == created_tenant.id
    assert found_tenant.name == test_tenant_data["name"]

@pytest.mark.unit
def test_user_repository_create(db_session, test_tenant_data, test_user_data):
    """测试用户Repository创建"""
    # 先创建租户
    tenant_repo = TenantRepository(db_session)
    tenant = Tenant(**test_tenant_data)
    tenant = tenant_repo.create(tenant)
    
    # 创建用户
    user_repo = UserRepository(db_session)
    user_data = test_user_data.copy()
    user_data["tenant_id"] = tenant.id
    user_data["password"] = password_hasher.hash_password(user_data["password"])
    user = User(**user_data)
    created_user = user_repo.create(user)
    
    assert created_user.id is not None
    assert created_user.username == test_user_data["username"]
    assert created_user.phone == test_user_data["phone"]

@pytest.mark.unit
def test_user_repository_get_by_phone(db_session, test_tenant_data, test_user_data):
    """测试用户Repository根据手机号查询"""
    # 先创建租户
    tenant_repo = TenantRepository(db_session)
    tenant = Tenant(**test_tenant_data)
    tenant = tenant_repo.create(tenant)
    
    # 创建用户
    user_repo = UserRepository(db_session)
    user_data = test_user_data.copy()
    user_data["tenant_id"] = tenant.id
    user_data["password"] = password_hasher.hash_password(user_data["password"])
    user = User(**user_data)
    user_repo.create(user)
    
    # 查询用户
    found_user = user_repo.get_by_phone(test_user_data["phone"])
    
    assert found_user is not None
    assert found_user.phone == test_user_data["phone"]
