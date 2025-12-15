"""
LLM服务测试
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.services.llm_service import LLMService
from app.services.config_service import ConfigService

@pytest.mark.unit
@pytest.mark.asyncio
async def test_llm_service_get_config():
    """测试获取LLM配置"""
    config_service = Mock(spec=ConfigService)
    config_repo = Mock()
    
    llm_service = LLMService(config_service, config_repo)
    
    # Mock config repository
    config_repo.list_user_configs.return_value = []
    config_repo.list_system_configs.return_value = []
    
    # Should raise ValueError when no config found
    with pytest.raises(ValueError, match="未找到LLM配置"):
        llm_service.get_llm_config(None, None)

@pytest.mark.unit
def test_llm_service_convert_messages():
    """测试消息格式转换"""
    config_service = Mock(spec=ConfigService)
    llm_service = LLMService(config_service)
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
    ]
    
    langchain_messages = llm_service._convert_messages(messages)
    
    assert len(langchain_messages) == 3
    assert langchain_messages[0].content == "You are a helpful assistant."
    assert langchain_messages[1].content == "Hello"
    assert langchain_messages[2].content == "Hi there!"
