"""
文件夹管理测试
"""
import pytest
from fastapi import status
from app.repositories.folder_repository import FolderRepository
from app.repositories.tenant_repository import TenantRepository
from app.repositories.user_repository import UserRepository
from app.models.folder import Folder
from app.models.tenant import Tenant
from app.models.user import User
from app.core.security import password_hasher, create_access_token

@pytest.fixture
def folder_auth_headers(client, db_session, test_tenant_data, test_user_data):
    """创建文件夹管理认证headers"""
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
    
    # 生成token
    token = create_access_token(data={"sub": user.id, "tenant_id": tenant.id})
    return {"Authorization": f"Bearer {token}"}, tenant, user

@pytest.mark.unit
def test_create_folder(client, folder_auth_headers):
    """测试创建文件夹"""
    headers, tenant, user = folder_auth_headers
    
    response = client.post(
        "/api/v1/folders",
        json={
            "name": "新文件夹",
            "tenant_id": tenant.id,
            "user_id": user.id,
            "parent_id": None
        },
        headers=headers
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "新文件夹"
    assert data["tenant_id"] == tenant.id

@pytest.mark.unit
def test_get_folders(client, folder_auth_headers, db_session):
    """测试获取文件夹列表"""
    headers, tenant, user = folder_auth_headers
    
    # 创建测试文件夹
    folder_repo = FolderRepository(db_session)
    folder = Folder(
        name="测试文件夹",
        tenant_id=tenant.id,
        user_id=user.id,
        parent_id=None
    )
    folder_repo.create(folder)
    
    response = client.get(
        f"/api/v1/folders?tenant_id={tenant.id}&user_id={user.id}",
        headers=headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

@pytest.mark.unit
def test_get_folder_by_id(client, folder_auth_headers, db_session):
    """测试根据ID获取文件夹"""
    headers, tenant, user = folder_auth_headers
    
    # 创建测试文件夹
    folder_repo = FolderRepository(db_session)
    folder = Folder(
        name="测试文件夹",
        tenant_id=tenant.id,
        user_id=user.id,
        parent_id=None
    )
    folder = folder_repo.create(folder)
    
    response = client.get(
        f"/api/v1/folders/{folder.id}",
        headers=headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == folder.id
    assert data["name"] == "测试文件夹"

@pytest.mark.unit
def test_update_folder(client, folder_auth_headers, db_session):
    """测试更新文件夹"""
    headers, tenant, user = folder_auth_headers
    
    # 创建测试文件夹
    folder_repo = FolderRepository(db_session)
    folder = Folder(
        name="测试文件夹",
        tenant_id=tenant.id,
        user_id=user.id,
        parent_id=None
    )
    folder = folder_repo.create(folder)
    
    response = client.put(
        f"/api/v1/folders/{folder.id}",
        json={
            "name": "更新后的文件夹",
            "tenant_id": tenant.id,
            "user_id": user.id,
            "parent_id": None
        },
        headers=headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "更新后的文件夹"

@pytest.mark.unit
def test_delete_folder(client, folder_auth_headers, db_session):
    """测试删除文件夹"""
    headers, tenant, user = folder_auth_headers
    
    # 创建测试文件夹
    folder_repo = FolderRepository(db_session)
    folder = Folder(
        name="测试文件夹",
        tenant_id=tenant.id,
        user_id=user.id,
        parent_id=None
    )
    folder = folder_repo.create(folder)
    
    response = client.delete(
        f"/api/v1/folders/{folder.id}",
        headers=headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    
    # 验证已删除
    deleted_folder = folder_repo.get_by_id(folder.id, tenant.id)
    assert deleted_folder is None or deleted_folder.deleted_at is not None
