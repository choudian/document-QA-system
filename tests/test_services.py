"""
服务层测试
"""
import pytest
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository
from app.repositories.tenant_repository import TenantRepository
from app.models.user import User
from app.models.tenant import Tenant
from app.core.security import password_hasher

@pytest.mark.unit
def test_auth_service_authenticate_user(db_session, test_tenant_data, test_user_data):
    """测试用户认证服务"""
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
    
    # 测试认证服务
    auth_service = AuthService(user_repo, tenant_repo)
    authenticated_user = auth_service.authenticate_user(
        phone=test_user_data["phone"],
        password=test_user_data["password"]
    )
    
    assert authenticated_user is not None
    assert authenticated_user.id == user.id
    assert authenticated_user.phone == test_user_data["phone"]

@pytest.mark.unit
def test_auth_service_authenticate_user_wrong_password(db_session, test_tenant_data, test_user_data):
    """测试错误密码认证"""
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
    
    # 测试认证服务
    auth_service = AuthService(user_repo, tenant_repo)
    authenticated_user = auth_service.authenticate_user(
        phone=test_user_data["phone"],
        password="wrong_password"
    )
    
    assert authenticated_user is None

@pytest.mark.unit
def test_password_hashing():
    """测试密码哈希"""
    password = "test_password_123"
    hashed = password_hasher.hash_password(password)
    
    assert hashed != password
    assert password_hasher.verify_password(password, hashed)
    assert not password_hasher.verify_password("wrong_password", hashed)
