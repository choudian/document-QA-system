"""
系统管理员 Schema
"""
from pydantic import BaseModel, Field, field_validator
import re


class SystemAdminInitRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50, description="管理员用户名")
    phone: str = Field(..., description="手机号（全局唯一）")
    password: str = Field(..., min_length=6, max_length=72, description="密码")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        phone_pattern = re.compile(r"^(\+86)?1[3-9]\d{9}$")
        normalized = v.replace("-", "").replace(" ", "")
        if not phone_pattern.match(normalized):
            raise ValueError("手机号格式不正确，请输入11位手机号")
        return normalized

