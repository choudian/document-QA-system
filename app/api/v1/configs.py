"""
配置管理API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.api.v1.me import get_current_user
from app.schemas.config import (
    ConfigUpdateRequest,
    ConfigListResponse,
    EffectiveConfigResponse,
    ConfigHistoryResponse,
    ConfigDefinitionsResponse,
)
from pydantic import BaseModel, Field
from typing import List
from app.repositories.config_repository import ConfigRepository
from app.services.config_service import ConfigService
from app.core.permissions import require_permission
from app.core.config_definitions import get_config_definitions_for_frontend

router = APIRouter()


def _build_service(db: Session) -> ConfigService:
    return ConfigService(
        config_repo=ConfigRepository(db),
    )


@router.get("", response_model=ConfigListResponse)
def list_configs(
    scope: str = "system",
    scope_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _=Depends(require_permission("system:config:read")),
):
    """
    按作用域列出配置（不合并）
    scope: system/tenant/user
    """
    # 租户管理员只能查看本租户
    if scope == "tenant" and not current_user.is_system_admin:
        scope_id = current_user.tenant_id
    if scope == "user" and not current_user.is_system_admin:
        scope_id = current_user.id

    service = _build_service(db)
    cfg = service.list_scope_configs(scope, scope_id)

    # 将字典展开为列表响应
    items = []
    for category, kv in cfg.items():
        for key, value in kv.items():
            items.append(
                {
                    "id": f"{scope}-{scope_id}-{category}-{key}",
                    "category": category,
                    "key": key,
                    "value": value,
                    "status": True,
                    "scope_type": scope,
                    "scope_id": scope_id,
                    "created_at": None,
                    "updated_at": None,
                    "created_by": None,
                }
            )
    return {"items": items}


@router.get("/effective", response_model=EffectiveConfigResponse)
def get_effective_config(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    获取当前用户/租户有效配置（已合并）
    """
    service = _build_service(db)
    cfg = service.get_effective_config(current_user.tenant_id, current_user.id)
    return {"configs": cfg}


@router.put("/system", status_code=status.HTTP_204_NO_CONTENT)
def update_system_config(
    payload: ConfigUpdateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _=Depends(require_permission("system:config:update")),
):
    service = _build_service(db)
    service.update_system_config(payload, operator_id=current_user.id)
    return None


@router.put("/tenant", status_code=status.HTTP_204_NO_CONTENT)
def update_tenant_config(
    payload: ConfigUpdateRequest,
    tenant_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _=Depends(require_permission("system:config:update")),
):
    # 租户管理员只能更新本租户
    if not current_user.is_system_admin:
        tenant_id = current_user.tenant_id
    if tenant_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="缺少 tenant_id")

    service = _build_service(db)
    service.update_tenant_config(tenant_id, payload, operator_id=current_user.id)
    return None


@router.put("/user", status_code=status.HTTP_204_NO_CONTENT)
def update_user_config(
    payload: ConfigUpdateRequest,
    user_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _=Depends(require_permission("system:config:update")),
):
    # 非系统管理员只能更新自身
    if not current_user.is_system_admin:
        user_id = current_user.id
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="缺少 user_id")

    service = _build_service(db)
    service.update_user_config(user_id, payload, operator_id=current_user.id)
    return None


@router.get("/history", response_model=ConfigHistoryResponse)
def list_history(
    scope_type: Optional[str] = None,
    scope_id: Optional[str] = None,
    category: Optional[str] = None,
    key: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _=Depends(require_permission("system:config:read")),
):
    service = _build_service(db)
    history = service.list_history(scope_type, scope_id, category, key)
    return {"items": history}


@router.post("/validate", status_code=status.HTTP_200_OK)
def validate_config(
    payload: ConfigUpdateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _=Depends(require_permission("system:config:update")),
):
    """
    校验接口占位（未实现具体规则）
    """
    service = _build_service(db)
    return service.validate_items(payload)


@router.get("/definitions", response_model=ConfigDefinitionsResponse)
def get_config_definitions(
    current_user=Depends(get_current_user),
):
    """
    获取配置项定义（用于前端动态渲染表单）
    根据用户角色过滤配置项：
    - 系统管理员：返回所有配置项定义
    - 租户管理员：返回所有配置项定义
    - 普通用户：返回空列表（不应该访问配置管理页面）
    """
    definitions = get_config_definitions_for_frontend(
        is_system_admin=current_user.is_system_admin,
        is_tenant_admin=current_user.is_tenant_admin
    )
    return {"definitions": definitions}


@router.get("/my-config", response_model=EffectiveConfigResponse)
def get_my_config(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _=Depends(require_permission("system:config:read")),
):
    """
    获取当前用户可配置的配置值
    - 系统管理员：返回系统级配置（如果不存在则返回空值）
    - 租户管理员：只返回租户级配置（如果不存在则返回空值，不展示系统默认配置）
    - 普通用户：返回403错误（不应该访问配置管理页面）
    """
    if not current_user.is_system_admin and not current_user.is_tenant_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="普通用户不能访问配置管理页面"
        )
    
    service = _build_service(db)
    
    if current_user.is_system_admin:
        # 系统管理员：返回系统级配置
        cfg = service.list_scope_configs("system", None)
    else:
        # 租户管理员：只返回租户级配置，不展示系统默认配置
        if not current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="租户管理员缺少tenant_id"
            )
        
        # 只返回租户级配置，如果不存在则返回空
        cfg = service.list_scope_configs("tenant", current_user.tenant_id)
    
    return {"configs": cfg}


@router.put("", status_code=status.HTTP_204_NO_CONTENT)
def update_config(
    payload: ConfigUpdateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _=Depends(require_permission("system:config:update")),
):
    """
    统一更新配置接口，根据用户角色自动判断配置层级
    - 系统管理员：更新系统级配置
    - 租户管理员：更新租户级配置；如果配置项为空或所有字段都为空，则删除该配置项（回退到系统级默认值）
    - 普通用户：返回403错误
    """
    if not current_user.is_system_admin and not current_user.is_tenant_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="普通用户不能访问配置管理页面"
        )
    
    service = _build_service(db)
    
    if current_user.is_system_admin:
        # 系统管理员：更新系统级配置
        service.update_system_config(payload, operator_id=current_user.id)
    elif current_user.is_tenant_admin:
        # 租户管理员：更新租户级配置
        if not current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="租户管理员缺少tenant_id"
            )
        service.update_tenant_config(current_user.tenant_id, payload, operator_id=current_user.id)
    
    return None


class ProbeRequest(BaseModel):
    """配置可用性探测请求"""
    category: str = Field(..., description="配置类别：llm/embedding/rerank/vector_store")
    key: str = Field("default", description="配置键")
    scope: str = Field("system", description="配置作用域：system/tenant/user")
    scope_id: Optional[str] = Field(None, description="作用域ID（租户ID或用户ID）")


class ProbeResponse(BaseModel):
    """配置可用性探测响应"""
    available: bool
    message: str
    latency_ms: Optional[int] = None


@router.post("/probe", response_model=ProbeResponse, status_code=status.HTTP_200_OK)
def probe_config_availability(
    payload: ProbeRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _=Depends(require_permission("system:config:read")),
):
    """
    探测配置可用性（占位实现）
    
    注意：此功能为占位实现，实际实现需要测试 API 连接、验证密钥等
    """
    import time
    
    start_time = time.time()
    
    try:
        service = _build_service(db)
        
        # 获取配置
        if payload.scope == "system":
            configs = service.list_scope_configs("system", None)
        elif payload.scope == "tenant":
            scope_id = payload.scope_id or current_user.tenant_id
            if not scope_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="租户级配置需要提供 tenant_id",
                )
            configs = service.list_scope_configs("tenant", scope_id)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="暂不支持用户级配置探测",
            )
        
        config_value = configs.get(payload.category, {}).get(payload.key)
        if not config_value:
            return ProbeResponse(
                available=False,
                message=f"配置 {payload.category}.{payload.key} 不存在",
                latency_ms=int((time.time() - start_time) * 1000),
            )
        
        # 占位：实际应该根据配置类型进行可用性检测
        # 例如：LLM 配置应该测试 API 连接，向量库配置应该测试连接等
        # TODO: 实现实际的可用性检测逻辑
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        return ProbeResponse(
            available=True,
            message="配置可用性检测成功（占位实现）",
            latency_ms=latency_ms,
        )
    except Exception as e:
        return ProbeResponse(
            available=False,
            message=f"配置可用性检测失败: {str(e)}",
            latency_ms=int((time.time() - start_time) * 1000) if 'start_time' in locals() else None,
        )


class ConfigCategoryResponse(BaseModel):
    """配置分类响应"""
    category: str = Field(..., description="分类名称")
    label: str = Field(..., description="分类标签")
    configs: List[str] = Field(..., description="配置项列表（category.key）")


@router.get("/categories", response_model=List[ConfigCategoryResponse], status_code=status.HTTP_200_OK)
def get_config_categories(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _=Depends(require_permission("system:config:read")),
):
    """
    获取配置项分类（占位实现）
    
    注意：此功能为占位实现，实际实现需要根据配置定义返回分类信息
    """
    # 占位：返回预定义的分类
    # TODO: 实际实现应该：
    # 1. 从配置定义中提取分类信息
    # 2. 按分类分组配置项
    # 3. 返回分类和对应的配置项列表
    
    categories = [
        {
            "category": "model",
            "label": "模型相关",
            "configs": ["llm.default", "rerank.default", "embedding.default"],
        },
        {
            "category": "storage",
            "label": "存储相关",
            "configs": ["vector_store.default"],
        },
        {
            "category": "document",
            "label": "文档相关",
            "configs": ["doc.upload", "doc.chunk"],
        },
        {
            "category": "qa",
            "label": "问答相关",
            "configs": ["retrieval.default"],
        },
        {
            "category": "system",
            "label": "系统相关",
            "configs": ["langfuse.default"],
        },
    ]
    
    return categories

