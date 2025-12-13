"""
配置项定义清单（OpenAI 风格）
用于校验、加密/脱敏和前端渲染参考
"""
from typing import Dict, Any, List, Optional
from app.schemas.config import ConfigDefinitionItem, FieldDefinition

# 每个字段定义：
# type: 期望类型
# required: 是否必填
# min/max: 数值范围
# allowed_values: 枚举/子集
# sensitive: 是否敏感（需要加密存储、脱敏回传）

# 配置项层级范围定义
# 2层配置（系统/租户）：embedding.default、vector_store.default、doc.upload、doc.chunk
# 3层配置（系统/租户/用户）：llm.default、rerank.default、retrieval.default
CONFIG_SCOPE_LEVELS: Dict[str, Dict[str, List[str]]] = {
    "embedding": {"default": ["system", "tenant"]},  # 2层
    "vector_store": {"default": ["system", "tenant"]},  # 2层
    "doc": {
        "upload": ["system", "tenant"],  # 2层
        "chunk": ["system", "tenant"]  # 2层
    },
    "llm": {"default": ["system", "tenant", "user"]},  # 3层
    "rerank": {"default": ["system", "tenant", "user"]},  # 3层
    "retrieval": {"default": ["system", "tenant", "user"]},  # 3层
}

CONFIG_DEFINITIONS: Dict[str, Dict[str, Dict[str, Any]]] = {
    "llm": {
        "default": {
            "provider": {"type": str, "required": True},
            "base_url": {"type": str, "required": True},
            "api_key": {"type": str, "required": True, "sensitive": True},
            "model": {"type": str, "required": True},
            "timeout": {"type": (int, float), "required": False, "min": 1, "max": 120},
            "temperature": {"type": (int, float), "required": False, "min": 0, "max": 1},
        }
    },
    "rerank": {
        "default": {
            "provider": {"type": str, "required": True},
            "base_url": {"type": str, "required": False},
            "api_key": {"type": str, "required": False, "sensitive": True},
            "model": {"type": str, "required": True},
        }
    },
    "embedding": {
        "default": {
            "provider": {"type": str, "required": True},
            "base_url": {"type": str, "required": False},
            "api_key": {"type": str, "required": False, "sensitive": True},
            "model": {"type": str, "required": True},
        }
    },
    "vector_store": {
        "default": {
            "provider": {"type": str, "required": True},
            "base_url": {"type": str, "required": True},
            "api_key": {"type": str, "required": False, "sensitive": True},
            "collection_prefix": {"type": str, "required": False},
        }
    },
    "doc": {
        "upload": {
            "upload_types": {"type": list, "required": True, "allowed_values": ["txt", "md", "pdf", "word"]},
            "max_file_size_mb": {"type": (int, float), "required": True, "min": 1, "max": 1024},
        },
        "chunk": {
            "strategy": {"type": str, "required": True, "allowed_values": ["fixed", "paragraph", "keyword"]},
            "size": {"type": (int, float), "required": True, "min": 1, "max": 5000},
            "overlap": {"type": (int, float), "required": True, "min": 0, "max": 4000},
        },
    },
    "retrieval": {
        "default": {
            "top_k": {"type": (int, float), "required": True, "min": 1, "max": 200},
            "similarity_threshold": {"type": (int, float), "required": True, "min": 0, "max": 1},
        }
    },
}

# 配置项显示标签映射
CONFIG_LABELS: Dict[str, Dict[str, str]] = {
    "llm": {"default": "LLM（默认）"},
    "rerank": {"default": "Rerank"},
    "embedding": {"default": "Embedding"},
    "vector_store": {"default": "向量库"},
    "doc": {"upload": "文档上传", "chunk": "文本切分"},
    "retrieval": {"default": "检索参数"},
}

# 字段显示标签映射
FIELD_LABELS: Dict[str, str] = {
    "provider": "Provider",
    "base_url": "Base URL",
    "api_key": "API Key",
    "model": "模型",
    "timeout": "超时(s)",
    "temperature": "Temperature",
    "collection_prefix": "Collection 前缀",
    "upload_types": "允许类型",
    "max_file_size_mb": "单文件大小(MB)",
    "strategy": "策略",
    "size": "chunk size",
    "overlap": "chunk overlap",
    "top_k": "topK",
    "similarity_threshold": "相似度阈值",
}

# 字段占位符映射
FIELD_PLACEHOLDERS: Dict[str, str] = {
    "provider": "openai / azure / aliyun ...",
    "base_url": "https://api.openai.com/v1",
    "api_key": "请输入密钥",
    "model": "gpt-4o-mini",
    "timeout": "",
    "temperature": "",
    "collection_prefix": "可选",
    "upload_types": "",
    "max_file_size_mb": "",
    "strategy": "",
    "size": "",
    "overlap": "",
    "top_k": "",
    "similarity_threshold": "",
}


def _python_type_to_frontend_type(python_type) -> str:
    """将 Python 类型转换为前端类型字符串"""
    if python_type == str:
        return "string"
    elif python_type in (int, float) or python_type == (int, float):
        return "number"
    elif python_type == bool:
        return "boolean"
    elif python_type == list:
        return "array"
    else:
        return "string"


def get_config_definitions_for_frontend(
    is_system_admin: bool = False,
    is_tenant_admin: bool = False
) -> List[ConfigDefinitionItem]:
    """
    将 CONFIG_DEFINITIONS 转换为前端可用的格式
    根据用户角色过滤配置项：
    - 系统管理员：返回所有配置项（系统级可配置）
    - 租户管理员：返回所有配置项（租户级可配置）
    - 普通用户：不返回任何配置项（用户级配置不在配置管理模块中处理）
    
    Args:
        is_system_admin: 是否为系统管理员
        is_tenant_admin: 是否为租户管理员
    
    Returns:
        配置项定义列表
    """
    # 普通用户不返回配置项
    if not is_system_admin and not is_tenant_admin:
        return []
    
    definitions = []
    
    for category, keys in CONFIG_DEFINITIONS.items():
        for key, fields_def in keys.items():
            field_list = []
            
            for field_name, field_meta in fields_def.items():
                python_type = field_meta.get("type", str)
                frontend_type = _python_type_to_frontend_type(python_type)
                
                field_def = FieldDefinition(
                    name=field_name,
                    type=frontend_type,
                    required=field_meta.get("required", False),
                    sensitive=field_meta.get("sensitive", False),
                    min=field_meta.get("min"),
                    max=field_meta.get("max"),
                    allowed_values=field_meta.get("allowed_values"),
                    label=FIELD_LABELS.get(field_name, field_name),
                    placeholder=FIELD_PLACEHOLDERS.get(field_name),
                )
                field_list.append(field_def)
            
            label = CONFIG_LABELS.get(category, {}).get(key, f"{category}.{key}")
            
            definitions.append(
                ConfigDefinitionItem(
                    category=category,
                    key=key,
                    label=label,
                    fields=field_list,
                )
            )
    
    return definitions

