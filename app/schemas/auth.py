"""
认证相关 Pydantic 模型
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


class RegisterRequest(BaseModel):
    """注册请求"""
    tenant_name: str = Field(..., min_length=2, max_length=128, description="租户名称")
    tenant_code: str = Field(..., min_length=2, max_length=64, description="租户编码")
    username: str = Field(..., min_length=3, max_length=64, description="用户名")
    # EmailStr 是 pydantic 提供的邮箱专用校验类型
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., min_length=6, max_length=64, description="密码")


class LoginRequest(BaseModel):
    """登录请求"""
    tenant_code: str = Field(..., description="租户编码")
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class TokenResponse(BaseModel):
    """Token 响应"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")


class UserResponse(BaseModel):
    """用户信息响应"""
    id: int
    tenant_id: int
    username: str
    email: str
    is_active: int
    is_super_admin: int
    last_login_at: Optional[str] = ""
    created_at: datetime

    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=64, description="新密码")
