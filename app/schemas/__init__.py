"""
Pydantic 模型
"""
from app.schemas.base import BaseResponse, PageResponse, PaginatedResponse
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    ChangePasswordRequest,
    TokenResponse,
    UserResponse,
    UserUpdateRequest,
)
from app.schemas.tenant import (
    TenantCreate,
    TenantUpdate,
    TenantResponse,
    TenantListResponse,
)
from app.schemas.department import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    DepartmentSimpleResponse,
)
from app.schemas.knowledge import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseResponse,
    KnowledgeBaseListResponse,
    DocumentResponse,
    DocumentListResponse,
    DocumentUploadResponse,
)
from app.schemas.chat import (
    ChatSessionCreate,
    ChatSessionResponse,
    ChatMessageCreate,
    ChatMessageResponse,
)
from app.schemas.user import (
    UserListResponse,
)

__all__ = [
    "BaseResponse",
    "PageResponse",
    "PaginatedResponse",
    "RegisterRequest",
    "LoginRequest",
    "ChangePasswordRequest",
    "TokenResponse",
    "UserResponse",
    "TenantCreate",
    "TenantUpdate",
    "TenantResponse",
    "TenantListResponse",
    "DepartmentCreate",
    "DepartmentUpdate",
    "DepartmentResponse",
    "DepartmentSimpleResponse",
    "KnowledgeBaseCreate",
    "KnowledgeBaseUpdate",
    "KnowledgeBaseResponse",
    "KnowledgeBaseListResponse",
    "DocumentResponse",
    "DocumentListResponse",
    "DocumentUploadResponse",
    "ChatSessionCreate",
    "ChatSessionResponse",
    "ChatMessageCreate",
    "ChatMessageResponse",
    "UserListResponse",
    "UserUpdateRequest",
]
