"""
API路由
"""
from fastapi import APIRouter

from app.api import auth, tenant

api_router = APIRouter()

# 认证路由（无需登录）
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])

api_router.include_router(tenant.router, prefix="/tenants", tags=["租户管理"])