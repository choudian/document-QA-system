"""
集成测试
"""
import pytest
from fastapi import status
from app.repositories.tenant_repository import TenantRepository
from app.repositories.user_repository import UserRepository
from app.repositories.folder_repository import FolderRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.conversation_repository import ConversationRepository
from app.models.tenant import Tenant
from app.models.user import User
from app.models.folder import Folder
from app.models.document import Document
from app.models.conversation import Conversation
from app.core.security import password_hasher, create_access_token

@pytest.mark.integration
def test_full_workflow(client, db_session, test_tenant_data, test_user_data):
    """测试完整工作流程：创建租户 -> 创建用户 -> 登录 -> 创建文件夹 -> 创建文档 -> 创建会话"""
    # 1. 创建租户
    tenant_repo = TenantRepository(db_session)
    tenant = Tenant(**test_tenant_data)
    tenant = tenant_repo.create(tenant)
    assert tenant.id is not None
    
    # 2. 创建用户
    user_repo = UserRepository(db_session)
    user_data = test_user_data.copy()
    user_data["tenant_id"] = tenant.id
    user_data["password"] = password_hasher.hash_password(user_data["password"])
    user = User(**user_data)
    user = user_repo.create(user)
    assert user.id is not None
    
    # 3. 登录
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "phone": test_user_data["phone"],
            "password": test_user_data["password"]
        }
    )
    assert login_response.status_code == status.HTTP_200_OK
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 4. 创建文件夹
    folder_response = client.post(
        "/api/v1/folders",
        json={
            "name": "工作文件夹",
            "tenant_id": tenant.id,
            "user_id": user.id,
            "parent_id": None
        },
        headers=headers
    )
    assert folder_response.status_code == status.HTTP_201_CREATED
    folder_id = folder_response.json()["id"]
    
    # 5. 创建文档（模拟）
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
        folder_id=folder_id,
        status="completed"
    )
    document = doc_repo.create(document)
    assert document.id is not None
    
    # 6. 创建会话
    conv_response = client.post(
        "/api/v1/qa/conversations",
        json={
            "title": "测试会话",
            "config": {
                "knowledge_base_ids": [folder_id],
                "top_k": 5
            }
        },
        headers=headers
    )
    assert conv_response.status_code == status.HTTP_201_CREATED
    conversation_id = conv_response.json()["id"]
    
    # 7. 验证所有数据都存在
    assert tenant_repo.get_by_id(tenant.id) is not None
    assert user_repo.get_by_id(user.id, tenant.id) is not None
    assert doc_repo.get_by_id(document.id, tenant.id) is not None
    assert ConversationRepository(db_session).get_by_id(conversation_id, tenant.id) is not None

@pytest.mark.integration
def test_multi_tenant_isolation(client, db_session, test_user_data):
    """测试多租户隔离"""
    # 创建两个租户
    tenant_repo = TenantRepository(db_session)
    tenant1 = Tenant(name="租户1", code="tenant1", status="active")
    tenant1 = tenant_repo.create(tenant1)
    tenant2 = Tenant(name="租户2", code="tenant2", status="active")
    tenant2 = tenant_repo.create(tenant2)
    
    # 为每个租户创建用户
    user_repo = UserRepository(db_session)
    user1_data = test_user_data.copy()
    user1_data["tenant_id"] = tenant1.id
    user1_data["phone"] = "13800000001"
    user1_data["password"] = password_hasher.hash_password(user1_data["password"])
    user1 = User(**user1_data)
    user1 = user_repo.create(user1)
    
    user2_data = test_user_data.copy()
    user2_data["tenant_id"] = tenant2.id
    user2_data["phone"] = "13800000002"
    user2_data["password"] = password_hasher.hash_password(user2_data["password"])
    user2 = User(**user2_data)
    user2 = user_repo.create(user2)
    
    # 验证用户只能看到自己租户的数据
    user1_list = user_repo.list_by_tenant(tenant1.id)
    user2_list = user_repo.list_by_tenant(tenant2.id)
    
    assert len(user1_list) == 1
    assert len(user2_list) == 1
    assert user1_list[0].id == user1.id
    assert user2_list[0].id == user2.id
    assert user1_list[0].tenant_id == tenant1.id
    assert user2_list[0].tenant_id == tenant2.id
