"""
文档管理测试
"""
import pytest
from fastapi import status
from app.repositories.document_repository import DocumentRepository
from app.repositories.folder_repository import FolderRepository
from app.repositories.tenant_repository import TenantRepository
from app.repositories.user_repository import UserRepository
from app.models.document import Document
from app.models.folder import Folder
from app.models.tenant import Tenant
from app.models.user import User
from app.core.security import password_hasher, create_access_token

@pytest.fixture
def document_auth_headers(client, db_session, test_tenant_data, test_user_data):
    """创建文档管理认证headers"""
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

@pytest.fixture
def test_folder(db_session, document_auth_headers):
    """创建测试文件夹"""
    _, tenant, user = document_auth_headers
    folder_repo = FolderRepository(db_session)
    folder = Folder(
        name="测试文件夹",
        tenant_id=tenant.id,
        user_id=user.id,
        parent_id=None
    )
    return folder_repo.create(folder)

@pytest.mark.unit
def test_get_documents_list(client, document_auth_headers, test_folder):
    """测试获取文档列表"""
    headers, tenant, user = document_auth_headers
    
    response = client.get(
        f"/api/v1/documents?tenant_id={tenant.id}&user_id={user.id}",
        headers=headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)

@pytest.mark.unit
def test_get_document_by_id(client, document_auth_headers, db_session, test_folder):
    """测试根据ID获取文档"""
    headers, tenant, user = document_auth_headers
    
    # 创建测试文档
    doc_repo = DocumentRepository(db_session)
    document = Document(
        name="test.txt",
        original_name="test.txt",
        file_type="txt",
        mime_type="text/plain",
        file_size=100,
        file_hash="test_hash",
        storage_path="/test/path",
        tenant_id=tenant.id,
        user_id=user.id,
        folder_id=test_folder.id,
        status="completed"
    )
    document = doc_repo.create(document)
    
    response = client.get(
        f"/api/v1/documents/{document.id}",
        headers=headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == document.id
    assert data["name"] == "test.txt"

@pytest.mark.unit
def test_delete_document(client, document_auth_headers, db_session, test_folder):
    """测试删除文档"""
    headers, tenant, user = document_auth_headers
    
    # 创建测试文档
    doc_repo = DocumentRepository(db_session)
    document = Document(
        name="test.txt",
        original_name="test.txt",
        file_type="txt",
        mime_type="text/plain",
        file_size=100,
        file_hash="test_hash",
        storage_path="/test/path",
        tenant_id=tenant.id,
        user_id=user.id,
        folder_id=test_folder.id,
        status="completed"
    )
    document = doc_repo.create(document)
    
    response = client.delete(
        f"/api/v1/documents/{document.id}",
        headers=headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    
    # 验证已软删除
    deleted_doc = doc_repo.get_by_id(document.id, tenant.id)
    assert deleted_doc is None or deleted_doc.deleted_at is not None

@pytest.mark.unit
def test_get_documents_by_folder(client, document_auth_headers, db_session, test_folder):
    """测试根据文件夹获取文档"""
    headers, tenant, user = document_auth_headers
    
    # 创建测试文档
    doc_repo = DocumentRepository(db_session)
    document = Document(
        name="test.txt",
        original_name="test.txt",
        file_type="txt",
        mime_type="text/plain",
        file_size=100,
        file_hash="test_hash",
        storage_path="/test/path",
        tenant_id=tenant.id,
        user_id=user.id,
        folder_id=test_folder.id,
        status="completed"
    )
    doc_repo.create(document)
    
    response = client.get(
        f"/api/v1/documents?tenant_id={tenant.id}&user_id={user.id}&folder_id={test_folder.id}",
        headers=headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert data[0]["folder_id"] == test_folder.id
