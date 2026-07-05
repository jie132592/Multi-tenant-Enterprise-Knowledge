"""租户管理API"""
from typing import List
from fastapi import APIRouter, Query, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import get_db
from app.api.deps import CurrentUser, get_current_user
from app.schemas import BaseResponse, KnowledgeBaseListResponse, KnowledgeBaseResponse, KnowledgeBaseCreate, \
    KnowledgeBaseUpdate
from app.services import KnowledgeService

router = APIRouter()


@router.get("", response_model=BaseResponse[List[KnowledgeBaseListResponse]])
def list_knowledge_bases(
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(20, ge=1, le=100, description="每页数量"),
        keyword: str = Query(None, description="搜索关键字"),
        current_user: CurrentUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    获取知识库列表
    """
    service = KnowledgeService(db)
    # 获取用户部门 ID
    user_department_id = current_user.user.department_id if current_user.user else None
    kbs, total = service.list(
        tenant_id=current_user.tenant_id,
        page=page,
        page_size=page_size,
        keyword=keyword,
        user_id=current_user.user_id,
        user_department_id=user_department_id
    )
    result = []
    for kb in kbs:
        result.append(KnowledgeBaseListResponse(
            id=kb.id,
            name=kb.name,
            description=kb.description,
            status=kb.status,
            visibility=kb.visibility,
            document_count=service.get_document_count(kb.id),
            paragraph_count=service.get_paragraph_count(kb.id),
            user_id=kb.user_id,
            department_id=kb.department_id,
            creator_username=service.get_creator_username(kb.user_id) if kb.user_id else "",
            created_at=kb.created_at
        ))
    return {
        "code": 200,
        "message": "成功",
        "data": result,
    }

@router.post("", response_model=BaseResponse[KnowledgeBaseResponse])
def create_knowledge_base(
    request: KnowledgeBaseCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建知识库
    """
    service = KnowledgeService(db)
    kb = service.create(
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
        name=request.name,
        description=request.description or "",
        visibility=request.visibility or "private",
        department_id=request.department_id
    )

    return {
        "code": 200,
        "message": "创建成功",
        "data": KnowledgeBaseResponse(
            id=kb.id,
            tenant_id=kb.tenant_id,
            user_id=kb.user_id,
            department_id=kb.department_id,
            name=kb.name,
            description=kb.description,
            status=kb.status,
            visibility=kb.visibility,
            document_count=0,
            paragraph_count=0,
            created_at=kb.created_at,
            updated_at=kb.updated_at
        )
    }


@router.get("/{kb_id}", response_model=BaseResponse[KnowledgeBaseResponse])
def get_knowledge_base(
    kb_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取知识库详情
    """
    service = KnowledgeService(db)
    kb = service.get(kb_id, current_user.tenant_id)

    if not kb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在")

    return {
        "code": 200,
        "message": "success",
        "data": KnowledgeBaseResponse(
            id=kb.id,
            tenant_id=kb.tenant_id,
            user_id=kb.user_id,
            department_id=kb.department_id,
            name=kb.name,
            description=kb.description,
            status=kb.status,
            visibility=kb.visibility,
            document_count=service.get_document_count(kb.id),
            paragraph_count=service.get_paragraph_count(kb.id),
            created_at=kb.created_at,
            updated_at=kb.updated_at
        )
    }


@router.put("/{kb_id}", response_model=BaseResponse[KnowledgeBaseResponse])
def update_knowledge_base(
    kb_id: int,
    request: KnowledgeBaseUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新知识库
    """
    service = KnowledgeService(db)
    kb = service.update(
        kb_id=kb_id,
        tenant_id=current_user.tenant_id,
        name=request.name,
        description=request.description,
        status=request.status,
        visibility=request.visibility,
        department_id=request.department_id
    )

    if not kb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在")

    return {
        "code": 200,
        "message": "更新成功",
        "data": KnowledgeBaseResponse(
            id=kb.id,
            tenant_id=kb.tenant_id,
            user_id=kb.user_id,
            department_id=kb.department_id,
            name=kb.name,
            description=kb.description,
            status=kb.status,
            visibility=kb.visibility,
            document_count=service.get_document_count(kb.id),
            paragraph_count=service.get_paragraph_count(kb.id),
            created_at=kb.created_at,
            updated_at=kb.updated_at
        )
    }


@router.delete("/{kb_id}", response_model=BaseResponse)
def delete_knowledge_base(
    kb_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除知识库
    需要知识库管理权限
    """
    from app.core.permissions import Permission, has_permission

    # 检查删除权限
    if not has_permission(current_user.user.role, Permission.KB_DELETE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要知识库删除权限"
        )

    service = KnowledgeService(db)
    success = service.delete(kb_id, current_user.tenant_id)

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在")

    return {
        "code": 200,
        "message": "删除成功"
    }
