"""
配置管理相关Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ConfigItem(BaseModel):
    category: str = Field(..., max_length=50, description="配置类别")
    key: str = Field(..., max_length=100, description="配置键")
    value: Any = Field(..., description="配置值（JSON兼容）")
    status: bool = Field(True, description="启用状态")


class ConfigUpdateRequest(BaseModel):
    items: List[ConfigItem] = Field(..., description="配置项列表")


class ConfigResponse(ConfigItem):
    id: str
    scope_type: str = Field(..., description="作用域：system/tenant/user")
    scope_id: Optional[str] = Field(None, description="作用域ID")
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]

    class Config:
        from_attributes = True


class EffectiveConfigResponse(BaseModel):
    """返回合并后的有效配置，按类别分组"""
    configs: Dict[str, Dict[str, Any]] = Field(..., description="configs[category][key]=value")


class ConfigHistoryItem(BaseModel):
    id: str
    scope_type: str
    scope_id: Optional[str]
    category: str
    key: str
    old_value: Optional[Any]
    new_value: Optional[Any]
    operator_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ConfigHistoryResponse(BaseModel):
    items: List[ConfigHistoryItem]


class ConfigListResponse(BaseModel):
    items: List[ConfigResponse]


class FieldDefinition(BaseModel):
    """字段定义"""
    name: str = Field(..., description="字段名")
    type: str = Field(..., description="字段类型：string/number/boolean/array")
    required: bool = Field(False, description="是否必填")
    sensitive: bool = Field(False, description="是否敏感字段（密码）")
    min: Optional[float] = Field(None, description="最小值（数值类型）")
    max: Optional[float] = Field(None, description="最大值（数值类型）")
    allowed_values: Optional[List[Any]] = Field(None, description="允许的值（枚举）")
    label: Optional[str] = Field(None, description="字段标签（显示名）")
    placeholder: Optional[str] = Field(None, description="占位符")


class ConfigDefinitionItem(BaseModel):
    """配置项定义"""
    category: str = Field(..., description="配置类别")
    key: str = Field(..., description="配置键")
    label: str = Field(..., description="显示标签")
    fields: List[FieldDefinition] = Field(..., description="字段定义列表")


class ConfigDefinitionsResponse(BaseModel):
    """配置定义响应"""
    definitions: List[ConfigDefinitionItem] = Field(..., description="配置定义列表")

