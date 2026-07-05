"""
部门相关 Pydantic 模型
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class DepartmentCreate(BaseModel):
    """创建部门请求"""
    name: str = Field(..., min_length=1, max_length=128, description="部门名称")
    code: str = Field(..., min_length=1, max_length=64, description="部门编码")
    parent_id: Optional[int] = Field(None, description="上级部门ID")
    description: Optional[str] = Field(default="", max_length=512, description="描述")


class DepartmentUpdate(BaseModel):
    """更新部门请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=128, description="部门名称")
    code: Optional[str] = Field(None, min_length=1, max_length=64, description="部门编码")
    parent_id: Optional[int] = Field(None, description="上级部门ID")
    leader_user_id: Optional[int] = Field(None, description="部门负责人ID")
    description: Optional[str] = Field(None, max_length=512, description="描述")


class DepartmentResponse(BaseModel):
    """部门响应"""
    id: int
    tenant_id: int
    name: str
    code: str
    parent_id: Optional[int] = None
    leader_user_id: Optional[int] = None
    leader_username: Optional[str] = ""
    description: str = ""
    user_count: int = Field(default=0, description="用户数量")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DepartmentSimpleResponse(BaseModel):
    """部门简单响应（用于下拉选择）"""
    id: int
    name: str
    code: str
    parent_id: Optional[int] = None

    class Config:
        from_attributes = True


class DepartmentWithChildrenResponse(BaseModel):
    """带子部门的部门响应"""
    id: int
    name: str
    code: str
    parent_id: Optional[int] = None
    description: str = ""
    user_count: int = 0
    children: List["DepartmentWithChildrenResponse"] = Field(default_factory=list)

    class Config:
        from_attributes = True
