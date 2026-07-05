"""
知识库相关 Pydantic 模型
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class KnowledgeBaseCreate(BaseModel):
    """创建知识库请求"""
    name: str = Field(..., min_length=1, max_length=256, description="知识库名称")
    description: Optional[str] = Field(default="", max_length=2000, description="描述")
    visibility: str = Field(default="private", description="可见性: public/department/private")
    department_id: Optional[int] = Field(None, description="部门ID（部门可见时使用）")


class KnowledgeBaseUpdate(BaseModel):
    """更新知识库请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=256, description="知识库名称")
    description: Optional[str] = Field(None, max_length=2000, description="描述")
    status: Optional[int] = Field(None, description="状态")
    visibility: Optional[str] = Field(None, description="可见性: public/department/private")
    department_id: Optional[int] = Field(None, description="部门ID")


class KnowledgeBaseResponse(BaseModel):
    """知识库响应"""
    id: int
    tenant_id: int
    user_id: Optional[int] = None
    department_id: Optional[int] = None
    name: str
    description: str
    status: int
    visibility: str = "private"
    document_count: int = Field(default=0, description="文档数量")
    paragraph_count: int = Field(default=0, description="段落数量")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class KnowledgeBaseListResponse(BaseModel):
    """知识库列表项响应"""
    id: int
    name: str
    description: str
    status: int
    visibility: str = "private"
    document_count: int = Field(default=0)
    paragraph_count: int = Field(default=0)
    user_id: Optional[int] = None
    department_id: Optional[int] = None
    creator_username: Optional[str] = ""
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    """文档响应"""
    id: int
    tenant_id: int
    kb_id: int
    name: str
    char_length: int
    status: int
    error_message: Optional[str] = ""
    paragraph_count: int = Field(default=0, description="段落数量")
    user_id: Optional[int] = None
    uploader_username: Optional[str] = ""
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """文档列表项响应"""
    id: int
    kb_id: int
    name: str
    char_length: int
    status: int
    paragraph_count: int = Field(default=0)
    uploader_username: Optional[str] = ""
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    """文档上传响应"""
    id: int
    name: str
    status: int
    char_length: int
    message: str = "文档上传成功"


class ParagraphResponse(BaseModel):
    """段落响应"""
    id: int
    doc_id: int
    content: str
    position: int
    is_active: int

    class Config:
        from_attributes = True
