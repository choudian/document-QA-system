"""
问答模块测试
"""
import pytest
from fastapi import status
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.tenant_repository import TenantRepository
from app.repositories.user_repository import UserRepository
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.tenant import Tenant
from app.models.user import User
from app.core.security import password_hasher, create_access_token

@pytest.fixture
def qa_auth_headers(client, db_session, test_tenant_data, test_user_data):
    """创建问答模块认证headers"""
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
def test_create_conversation(client, qa_auth_headers):
    """测试创建会话"""
    headers, tenant, user = qa_auth_headers
    
    response = client.post(
        "/api/v1/qa/conversations",
        json={
            "title": "测试会话",
            "config": {
                "knowledge_base_ids": [],
                "top_k": 5,
                "similarity_threshold": 0.7
            }
        },
        headers=headers
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == "测试会话"
    assert data["tenant_id"] == tenant.id
    assert data["user_id"] == user.id

@pytest.mark.unit
def test_get_conversations(client, qa_auth_headers, db_session):
    """测试获取会话列表"""
    headers, tenant, user = qa_auth_headers
    
    # 创建测试会话
    conv_repo = ConversationRepository(db_session)
    conversation = Conversation(
        title="测试会话",
        tenant_id=tenant.id,
        user_id=user.id,
        status="active"
    )
    conv_repo.create(conversation)
    
    response = client.get(
        f"/api/v1/qa/conversations?tenant_id={tenant.id}&user_id={user.id}",
        headers=headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

@pytest.mark.unit
def test_get_conversation_by_id(client, qa_auth_headers, db_session):
    """测试根据ID获取会话"""
    headers, tenant, user = qa_auth_headers
    
    # 创建测试会话
    conv_repo = ConversationRepository(db_session)
    conversation = Conversation(
        title="测试会话",
        tenant_id=tenant.id,
        user_id=user.id,
        status="active"
    )
    conversation = conv_repo.create(conversation)
    
    response = client.get(
        f"/api/v1/qa/conversations/{conversation.id}",
        headers=headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == conversation.id
    assert data["title"] == "测试会话"

@pytest.mark.unit
def test_delete_conversation(client, qa_auth_headers, db_session):
    """测试删除会话"""
    headers, tenant, user = qa_auth_headers
    
    # 创建测试会话
    conv_repo = ConversationRepository(db_session)
    conversation = Conversation(
        title="测试会话",
        tenant_id=tenant.id,
        user_id=user.id,
        status="active"
    )
    conversation = conv_repo.create(conversation)
    
    response = client.delete(
        f"/api/v1/qa/conversations/{conversation.id}",
        headers=headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    
    # 验证已删除
    deleted_conv = conv_repo.get_by_id(conversation.id, tenant.id)
    assert deleted_conv is None or deleted_conv.deleted_at is not None

@pytest.mark.unit
def test_get_messages(client, qa_auth_headers, db_session):
    """测试获取消息列表"""
    headers, tenant, user = qa_auth_headers
    
    # 创建测试会话
    conv_repo = ConversationRepository(db_session)
    conversation = Conversation(
        title="测试会话",
        tenant_id=tenant.id,
        user_id=user.id,
        status="active"
    )
    conversation = conv_repo.create(conversation)
    
    # 创建测试消息
    msg_repo = MessageRepository(db_session)
    message = Message(
        conversation_id=conversation.id,
        tenant_id=tenant.id,
        user_id=user.id,
        role="user",
        content="测试消息",
        sequence=1
    )
    msg_repo.create(message)
    
    response = client.get(
        f"/api/v1/qa/conversations/{conversation.id}/messages",
        headers=headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "messages" in data
    assert isinstance(data["messages"], list)
    if len(data["messages"]) > 0:
        assert data["messages"][0]["content"] == "测试消息"
