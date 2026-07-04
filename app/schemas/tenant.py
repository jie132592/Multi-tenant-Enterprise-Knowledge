"""
租户相关 Pydantic 模型
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class TenantBase(BaseModel):
    """租户基础模型"""
    name: str = Field(..., min_length=2, max_length=128, description="租户名称")
    code: str = Field(..., min_length=2, max_length=64, description="租户编码")
    description: Optional[str] = Field(default="", max_length=512, description="描述")


class TenantCreate(TenantBase):
    """创建租户请求"""
    pass


class TenantUpdate(BaseModel):
    """更新租户请求"""
    name: Optional[str] = Field(None, min_length=2, max_length=128, description="租户名称")
    description: Optional[str] = Field(None, max_length=512, description="描述")
    status: Optional[int] = Field(None, description="状态: 1=正常 0=禁用")


class TenantResponse(BaseModel):
    """租户响应"""
    id: int
    name: str
    code: str
    status: int
    description: Optional[str] = ""
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TenantListResponse(BaseModel):
    """租户列表项响应"""
    id: int
    name: str
    code: str
    status: int
    description: Optional[str] = ""
    user_count: int = Field(default=0, description="用户数量")
    kb_count: int = Field(default=0, description="知识库数量")
    created_at: datetime

    class Config:
        from_attributes = True
