"""
基础 Pydantic 模型
"""
from typing import Generic, TypeVar, Optional, Any, List
from pydantic import BaseModel, Field

T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    """统一响应格式"""
    code: int = Field(default=200, description="状态码")
    message: str = Field(default="success", description="消息")
    data: Optional[T] = Field(default=None, description="数据")


class PageResponse(BaseModel):
    """分页信息"""
    total: int = Field(default=0, description="总数")
    page: int = Field(default=1, description="当前页")
    page_size: int = Field(default=20, description="每页数量")
    total_pages: int = Field(default=0, description="总页数")


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应"""
    items: List[T] = Field(default_factory=list, description="数据列表")
    page: int = Field(default=1, description="当前页")
    page_size: int = Field(default=20, description="每页数量")
    total: int = Field(default=0, description="总数")


class ErrorResponse(BaseModel):
    """错误响应"""
    code: int = Field(default=400, description="错误码")
    message: str = Field(..., description="错误信息")
    detail: Optional[str] = Field(default=None, description="详细错误信息")


def success_response(data: Any = None, message: str = "success") -> dict:
    """快速构建成功响应"""
    return {"code": 200, "message": message, "data": data}


def error_response(code: int = 400, message: str = "error", detail: str = None) -> dict:
    """快速构建错误响应"""
    return {"code": code, "message": message, "detail": detail}
