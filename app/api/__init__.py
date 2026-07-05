"""
API 路由
"""
from fastapi import APIRouter

from app.api import auth, tenant, department, knowledge, document, chat

api_router = APIRouter()

# 认证路由（无需登录）
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])

# 租户路由
api_router.include_router(tenant.router, prefix="/tenants", tags=["租户管理"])

# 部门路由
api_router.include_router(department.router, prefix="/departments", tags=["部门管理"])

# 知识库路由
api_router.include_router(knowledge.router, prefix="/kb", tags=["知识库"])

# 文档路由
api_router.include_router(document.router, prefix="/documents", tags=["文档管理"])

# 对话路由
api_router.include_router(chat.router, prefix="/chat", tags=["对话"])
