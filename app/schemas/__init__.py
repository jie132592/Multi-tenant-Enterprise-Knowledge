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
)
from app.schemas.tenant import (
    TenantCreate,
    TenantUpdate,
    TenantResponse,
    TenantListResponse,
)
from app.schemas.knowledge import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseResponse,
    DocumentResponse,
)
from app.schemas.chat import (
    ChatSessionCreate,
    ChatSessionResponse,
    ChatMessageCreate,
    ChatMessageResponse,
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
    "KnowledgeBaseCreate",
    "KnowledgeBaseUpdate",
    "KnowledgeBaseResponse",
    "DocumentResponse",
    "ChatSessionCreate",
    "ChatSessionResponse",
    "ChatMessageCreate",
    "ChatMessageResponse",
]
