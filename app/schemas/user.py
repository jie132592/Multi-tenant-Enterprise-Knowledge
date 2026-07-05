"""
用户相关 Pydantic 模型
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class UserListResponse(BaseModel):
    """用户列表响应"""
    id: int
    tenant_id: int
    username: str
    email: str
    role: str = "member"
    is_active: int
    is_super_admin: int
    is_tenant_admin: int
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    last_login_at: Optional[str] = ""
    created_at: datetime

    class Config:
        from_attributes = True


class UserListRequest(BaseModel):
    """用户列表请求"""
    keyword: Optional[str] = Field(None, description="搜索关键词")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
