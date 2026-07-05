from typing import List

from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from app import get_db_session, get_db
from app.api.deps import CurrentUser, require_super_admin
from app.models import Tenant, User
from app.models.knowledge import KnowledgeBase
from app.schemas import BaseResponse, TenantListResponse, TenantCreate, TenantResponse, TenantUpdate

router = APIRouter()


@router.get("/", response_model=BaseResponse[List[TenantListResponse]])
def list_tenants(
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(10, ge=1, description="每页数量"),
        key_word: str = Query(None, description="关键词"),
        db: Session = Depends(get_db)
):
    """
    获取租户列表（超级管理员专用）
    """
    query = db.query(Tenant)

    if key_word:
        query = query.filter(Tenant.name.like(f"%{key_word}%") | Tenant.code.like(f"%{key_word}%"))

    total = query.count()

    # 分页
    # order_by: 按...排序
    # 按创建时间倒叙
    tenants = query.order_by(Tenant.created_at.desc()) \
        .offset((page - 1) * page_size) \
        .limit(page_size).all()

    # 补充信息
    result = []
    for tenant in tenants:
        user_count = db.query(User).filter(User.tenant_id == tenant.id).count()
        kb_count = db.query(KnowledgeBase).filter(KnowledgeBase.tenant_id == tenant.id).count()
        item = TenantListResponse(
            id=tenant.id,
            name=tenant.name,
            code=tenant.code,
            status=tenant.status,
            description=tenant.description,
            user_count=user_count,
            kb_count=kb_count,
            created_at=tenant.created_at,
        )
        result.append(item)

    return {
        "code": 200,
        "message": "成功",
        "data": result,
    }


@router.post("/create-tenant", response_model=BaseResponse[TenantResponse])
def create_tenant(
        request: TenantCreate,
        db: Session = Depends(get_db),
):
    """创建租户"""
    code = db.query(Tenant).filter(Tenant.code == request.code).first()
    if code:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="租户编码已存在")

    tenant = Tenant(
        name=request.name,
        code=request.code,
        status=1,
        description=request.description or "",
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    return {
        "code": 200,
        "message": "创建成功",
        "data": TenantResponse.model_validate(tenant),
    }


@router.get("/{tenant_id}", response_model=BaseResponse[TenantResponse])
def get_tenant(tenant_id: int, db: Session = Depends(get_db)):
    """获取租户详情"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="租户不存在")

    return {
        "code": 200,
        "message": "成功",
        "data": TenantResponse.model_validate(tenant),
    }


@router.put("/{tenant_id}", response_model=BaseResponse[TenantResponse])
def update_tenant(
        tenant_id: int,
        request: TenantUpdate,
        db: Session = Depends(get_db),
):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="租户不存在")

    if request.name is not None:
        tenant.name = request.name
    if request.description is not None:
        tenant.description = request.description
    if request.status is not None:
        tenant.status = request.status

    db.commit()
    db.refresh(tenant)
    return {
        "code": 200,
        "message": "更新成功",
        "data": TenantResponse.model_validate(tenant),
    }


@router.delete("/{tenant_id}", response_model=BaseResponse)
def delete_tenant(
        tenant_id: int,
        current: CurrentUser = Depends(require_super_admin),
        db: Session = Depends(get_db)
):
    """
    删除租户（超级管理员专用）

    - 删除租户会级联删除所有关联数据（用户、知识库、文档等）
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="租户不存在")

    if current.tenant_id == tenant_id:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="不能删除自己所在的租户")

    db.delete(tenant)
    db.commit()

    return {
        "code": 200,
        "message": "删除成功",
    }
