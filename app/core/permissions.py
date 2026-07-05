"""
权限定义模块

角色权限体系：
- super_admin: 超级管理员，系统级，可管理所有租户
- tenant_admin: 租户管理员，可管理本租户内所有资源
- member: 普通成员，受限于所在部门的资源访问

权限标识：
- kb:manage - 知识库管理
- kb:create - 创建知识库
- kb:delete - 删除知识库
- doc:upload - 上传文档
- doc:delete - 删除文档
- dept:manage - 部门管理
- user:manage - 用户管理（分配部门、角色等）
"""
from enum import Enum

from app.models import UserRole


class Permission(str, Enum):
    # 知识库权限
    KB_MANAGE = "kb:manage"  # 管理知识库
    KB_CREATE = "kb:create"  # 创建知识库
    KB_DELETE = "kb:delete"  # 删除知识库

    # 文档权限
    DOC_UPLOAD = "doc:upload"  # 上传文档
    DOC_DELETE = "doc:delete"  # 删除文档

    # 部门权限
    DEPT_MANAGE = "dept:manage"  # 管理部门

    # 用户权限
    USER_MANAGE = "user:manage"  # 管理用户


# 角色权限映射
ROLE_PERMISSIONS = {
    UserRole.SUPER_ADMIN: {
        # 系统级管理员拥有所有权限
        Permission.KB_MANAGE,
        Permission.KB_CREATE,
        Permission.KB_DELETE,
        Permission.DOC_UPLOAD,
        Permission.DOC_DELETE,
        Permission.DEPT_MANAGE,
        Permission.USER_MANAGE,
    },
    UserRole.TENANT_ADMIN: {
        Permission.KB_MANAGE,
        Permission.KB_CREATE,
        Permission.KB_DELETE,
        Permission.DOC_UPLOAD,
        Permission.DOC_DELETE,
        Permission.DEPT_MANAGE,
        Permission.USER_MANAGE,
    },
    UserRole.MEMBER: {
        Permission.KB_CREATE,
        Permission.DOC_UPLOAD
    }
}

def has_permission(role: str, permission: Permission) -> bool:
    """检测角色是否拥有指定权限"""
    if role not in ROLE_PERMISSIONS:
        return False
    return permission in ROLE_PERMISSIONS[role]

def require_permission(role: str, permission: Permission) -> bool:
    """检查权限"""
    if not has_permission(role, permission):
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"权限不足，需要 {permission.value} 权限")
    return True