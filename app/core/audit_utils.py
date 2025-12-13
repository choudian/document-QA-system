"""
审计日志工具函数
"""
import json
from typing import Any, Dict, List, Union


# 默认敏感字段列表
DEFAULT_SENSITIVE_FIELDS = [
    'password',
    'password_hash',
    'api_key',
    'apiKey',
    'secret',
    'secret_key',
    'token',
    'access_token',
    'refresh_token',
    'authorization',
    'auth',
    'credential',
    'credentials',
]


def mask_value(value: str, keep_start: int = 4, keep_end: int = 4) -> str:
    """
    脱敏单个值
    保留前keep_start个字符和后keep_end个字符，中间用****替代
    
    Args:
        value: 要脱敏的值
        keep_start: 保留前N个字符
        keep_end: 保留后N个字符
    
    Returns:
        脱敏后的值
    """
    if not isinstance(value, str) or len(value) <= keep_start + keep_end:
        return '****'
    
    start = value[:keep_start]
    end = value[-keep_end:] if keep_end > 0 else ''
    return f"{start}****{end}"


def mask_sensitive_data(data: Any, sensitive_fields: List[str] = None) -> Any:
    """
    递归脱敏数据中的敏感字段
    
    Args:
        data: 要脱敏的数据（可以是dict、list、str等）
        sensitive_fields: 敏感字段列表，如果为None则使用默认列表
    
    Returns:
        脱敏后的数据
    """
    if sensitive_fields is None:
        sensitive_fields = DEFAULT_SENSITIVE_FIELDS
    
    if data is None:
        return None
    
    # 如果是字符串，直接返回（不脱敏字符串本身）
    if isinstance(data, str):
        return data
    
    # 如果是字典，递归处理每个字段
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            # 检查字段名是否在敏感字段列表中（不区分大小写）
            key_lower = key.lower()
            is_sensitive = any(sf.lower() in key_lower or key_lower in sf.lower() for sf in sensitive_fields)
            
            if is_sensitive and isinstance(value, str):
                # 敏感字段且值为字符串，进行脱敏
                result[key] = mask_value(value)
            elif isinstance(value, (dict, list)):
                # 嵌套结构，递归处理
                result[key] = mask_sensitive_data(value, sensitive_fields)
            else:
                # 其他类型，直接复制
                result[key] = value
        return result
    
    # 如果是列表，递归处理每个元素
    if isinstance(data, list):
        return [mask_sensitive_data(item, sensitive_fields) for item in data]
    
    # 其他类型，直接返回
    return data


def serialize_for_storage(data: Any, max_size: int = 100000) -> str:
    """
    序列化数据为JSON字符串，用于存储
    
    Args:
        data: 要序列化的数据
        max_size: 最大大小（字节），超过则截断
    
    Returns:
        JSON字符串
    """
    try:
        json_str = json.dumps(data, ensure_ascii=False)
        # 如果超过最大大小，截断
        if len(json_str.encode('utf-8')) > max_size:
            # 截断到最大大小（保留UTF-8字符完整性）
            bytes_data = json_str.encode('utf-8')[:max_size]
            # 尝试解码，如果失败则去掉最后一个不完整的字符
            try:
                json_str = bytes_data.decode('utf-8')
            except UnicodeDecodeError:
                json_str = bytes_data[:-1].decode('utf-8')
            json_str += '...(truncated)'
        return json_str
    except (TypeError, ValueError) as e:
        # 如果无法序列化，返回错误信息
        return f'[Serialization Error: {str(e)}]'

