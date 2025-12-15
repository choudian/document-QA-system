"""
用户Schema
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
import re


class UserBase(BaseModel):
    """用户基础Schema"""
    username: str = Field(..., min_length=1, max_length=50, description="用户名")
    phone: str = Field(..., description="手机号（必填，用作登录账号）")
    
    # @field_validator('phone')
    # @classmethod
    # def validate_phone(cls, v):
    #     if v is None or v == '':
    #         raise ValueError('手机号不能为空')
    #     # 简单的手机号验证：11位数字，可以以+86开头
    #     phone_pattern = re.compile(r'^(\+86)?1[3-9]\d{9}$')
    #     normalized = v.replace('-', '').replace(' ', '')
    #     if not phone_pattern.match(normalized):
    #         raise ValueError('手机号格式不正确，请输入11位手机号')
    #     return normalized


class UserCreate(UserBase):
    """创建用户Schema"""
    tenant_id: str = Field(..., description="租户ID")
    password: str = Field(..., min_length=6, max_length=72, description="密码（最长72字符）")
    is_system_admin: bool = Field(False, description="是否为系统管理员（租户为空）")


class UserUpdate(BaseModel):
    """更新用户Schema"""
    username: Optional[str] = Field(None, min_length=1, max_length=50, description="用户名")
    phone: Optional[str] = Field(None, description="手机号")
    password: Optional[str] = Field(None, min_length=6, max_length=72, description="密码（最长72字符）")
    status: Optional[str] = Field(None, description="状态：active-启用，frozen-冻结")
    is_system_admin: Optional[bool] = Field(None, description="是否为系统管理员（租户为空）")
    tenant_id: Optional[str] = Field(None, description="租户ID（仅系统管理员可修改）")
    
    # @field_validator('phone')
    # @classmethod
    # def validate_phone(cls, v):
    #     if v is None or v == '':
    #         return None
    #     # 简单的手机号验证：11位数字，可以以+86开头
    #     phone_pattern = re.compile(r'^(\+86)?1[3-9]\d{9}$')
    #     if not phone_pattern.match(v.replace('-', '').replace(' ', '')):
    #         raise ValueError('手机号格式不正确，请输入11位手机号')
    #     return v.replace('-', '').replace(' ', '')


class UserResponse(UserBase):
    """用户响应Schema"""
    id: str
    tenant_id: Optional[str]
    status: str
    is_tenant_admin: bool
    is_system_admin: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    
    class Config:
        from_attributes = True


class UserInviteRequest(BaseModel):
    """用户邀请请求"""
    email: Optional[str] = Field(None, description="邮箱地址（可选）")
    phone: str = Field(..., description="手机号")
    username: Optional[str] = Field(None, description="用户名（可选，默认使用手机号）")
    role_ids: Optional[List[str]] = Field(None, description="角色ID列表（可选）")


class UserInviteResponse(BaseModel):
    """用户邀请响应"""
    invite_code: str = Field(..., description="邀请码")
    invite_url: str = Field(..., description="邀请链接")
    expires_at: str = Field(..., description="过期时间（ISO 格式）")


class UserImportRequest(BaseModel):
    """用户批量导入请求"""
    file_url: Optional[str] = Field(None, description="文件URL（可选）")
    file_content: Optional[str] = Field(None, description="文件内容（Base64编码，可选）")
    file_type: str = Field("excel", description="文件类型：excel/csv")


class UserImportResponse(BaseModel):
    """用户批量导入响应"""
    total: int = Field(..., description="总记录数")
    success: int = Field(..., description="成功数")
    failed: int = Field(..., description="失败数")
    errors: List[dict] = Field(default_factory=list, description="错误详情")
