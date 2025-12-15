"""
配置服务测试
"""
import pytest
import json
from app.services.config_service import ConfigService
from app.repositories.config_repository import ConfigRepository
from app.models.config import Config

@pytest.mark.unit
def test_config_service_get_effective_config(db_session):
    """测试获取有效配置（系统级）"""
    config_repo = ConfigRepository(db_session)
    config_service = ConfigService(config_repo)
    
    # 创建系统级配置
    system_config = Config(
        category="llm",
        key="default",
        tenant_id=None,
        user_id=None,
        value=json.dumps({
            "model": "gpt-4",
            "temperature": 0.7
        })
    )
    config_repo.create(system_config)
    
    # 获取有效配置
    effective_config = config_service.get_effective_config(None, None)
    llm_config = effective_config.get("llm", {}).get("default")
    
    assert llm_config is not None
    assert llm_config["model"] == "gpt-4"
    assert llm_config["temperature"] == 0.7

@pytest.mark.unit
def test_config_service_tenant_override(db_session, test_tenant_data):
    """测试租户级配置覆盖系统级配置"""
    from app.repositories.tenant_repository import TenantRepository
    
    config_repo = ConfigRepository(db_session)
    tenant_repo = TenantRepository(db_session)
    config_service = ConfigService(config_repo)
    
    # 创建租户
    tenant = Tenant(**test_tenant_data)
    tenant = tenant_repo.create(tenant)
    
    # 创建系统级配置
    system_config = Config(
        category="llm",
        key="default",
        tenant_id=None,
        user_id=None,
        value=json.dumps({
            "model": "gpt-4",
            "temperature": 0.7
        })
    )
    config_repo.create(system_config)
    
    # 创建租户级配置（覆盖temperature）
    tenant_config = Config(
        category="llm",
        key="default",
        tenant_id=tenant.id,
        user_id=None,
        value=json.dumps({
            "temperature": 0.9
        })
    )
    config_repo.create(tenant_config)
    
    # 获取有效配置（应该合并系统级和租户级）
    effective_config = config_service.get_effective_config(tenant.id, None)
    llm_config = effective_config.get("llm", {}).get("default")
    
    assert llm_config is not None
    assert llm_config["model"] == "gpt-4"  # 来自系统级
    assert llm_config["temperature"] == 0.9  # 来自租户级（覆盖）
