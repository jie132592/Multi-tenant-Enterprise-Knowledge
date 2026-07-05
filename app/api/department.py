"""
部门管理 API
"""
from typing import List

from fastapi import APIRouter, Query, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import get_db
from app.api.deps import CurrentUser, get_current_user
from app.models import Department
from app.schemas import DepartmentResponse, BaseResponse, DepartmentCreate, DepartmentUpdate
from app.services import DepartmentService

router = APIRouter()

@router.get("", response_model=BaseResponse[List[DepartmentResponse]])
def list_departments(
        keyword: str = Query(None, description="搜索关键字"),
        current_user: CurrentUser= Depends(get_current_user),
        db: Session = Depends(get_db)

):
    service = DepartmentService(db)
    depts, total = service.list(
        tenant_id=current_user.tenant_id,
        keyword=keyword,
    )
    result = []
    for dept in depts:
        result.append(DepartmentResponse(
            id=dept.id,
            tenant_id=dept.tenant_id,
            name=dept.name,
            code=dept.code,
            parent_id=dept.parent_id,
            leader_user_id=dept.leader_user_id,
            leader_username=service.get_leader_username(dept.leader_user_id) if dept.leader_user_id else "",
            description=dept.description or "",
            user_count=service.get_user_count(dept.id),
            created_at=dept.created_at,
            updated_at=dept.updated_at
        ))

    return {
        "code": 200,
        "message": "success",
        "data": result,
    }

@router.get("/tree", response_model=BaseResponse)
def get_department_tree(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取部门树形结构
    """
    service = DepartmentService(db)
    tree = service.build_tree(current_user.tenant_id)

    return {
        "code": 200,
        "message": "success",
        "data": tree
    }

@router.post("", response_model=BaseResponse[DepartmentResponse])
def create_department(
    request: DepartmentCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建部门（仅租户管理员）
    """
    if not current_user.user.is_super_admin and not current_user.user.is_tenant_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅管理员可创建部门"
        )

    service = DepartmentService(db)

    # 检查编码是否已存在
    existing = db.query(Department).filter(
        Department.tenant_id == current_user.tenant_id,
        Department.code == request.code
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="部门编码已存在")

    # 检查父部门
    if request.parent_id:
        parent = service.get(request.parent_id, current_user.tenant_id)
        if not parent:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="父部门不存在")

    dept = service.create(
        tenant_id=current_user.tenant_id,
        name=request.name,
        code=request.code,
        parent_id=request.parent_id,
        description=request.description or ""
    )

    return {
        "code": 200,
        "message": "创建成功",
        "data": DepartmentResponse(
            id=dept.id,
            tenant_id=dept.tenant_id,
            name=dept.name,
            code=dept.code,
            parent_id=dept.parent_id,
            leader_user_id=dept.leader_user_id,
            leader_username="",
            description=dept.description or "",
            user_count=0,
            created_at=dept.created_at,
            updated_at=dept.updated_at
        )
    }

@router.get("/{dept_id}", response_model=BaseResponse[DepartmentResponse])
def get_department(
    dept_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取部门详情
    """
    service = DepartmentService(db)
    dept = service.get(dept_id, current_user.tenant_id)
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="部门不存在")

    return {
        "code": 200,
        "message": "success",
        "data": DepartmentResponse(
            id=dept.id,
            tenant_id=dept.tenant_id,
            name=dept.name,
            code=dept.code,
            parent_id=dept.parent_id,
            leader_user_id=dept.leader_user_id,
            leader_username=service.get_leader_username(dept.leader_user_id) if dept.leader_user_id else "",
            description=dept.description or "",
            user_count=service.get_user_count(dept.id),
            created_at=dept.created_at,
            updated_at=dept.updated_at
        )
    }

@router.put("/{dept_id}", response_model=BaseResponse[DepartmentResponse])
def update_department(
    dept_id: int,
    request: DepartmentUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新部门（仅租户管理员）
    """
    if not current_user.user.is_super_admin and not current_user.user.is_tenant_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅管理员可更新部门"
        )

    service = DepartmentService(db)

    # 检查编码是否冲突
    if request.code:
        existing = db.query(Department).filter(
            Department.tenant_id == current_user.tenant_id,
            Department.code == request.code,
            Department.id != dept_id
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="部门编码已存在")

    dept = service.update(
        dept_id=dept_id,
        tenant_id=current_user.tenant_id,
        name=request.name,
        code=request.code,
        parent_id=request.parent_id,
        leader_user_id=request.leader_user_id,
        description=request.description
    )

    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="部门不存在")

    return {
        "code": 200,
        "message": "更新成功",
        "data": DepartmentResponse(
            id=dept.id,
            tenant_id=dept.tenant_id,
            name=dept.name,
            code=dept.code,
            parent_id=dept.parent_id,
            leader_user_id=dept.leader_user_id,
            leader_username=service.get_leader_username(dept.leader_user_id) if dept.leader_user_id else "",
            description=dept.description or "",
            user_count=service.get_user_count(dept.id),
            created_at=dept.created_at,
            updated_at=dept.updated_at
        )
    }


@router.delete("/{dept_id}", response_model=BaseResponse)
def delete_department(
    dept_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除部门（仅租户管理员）
    """
    if not current_user.user.is_super_admin and not current_user.user.is_tenant_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅管理员可删除部门"
        )

    service = DepartmentService(db)

    try:
        success = service.delete(dept_id, current_user.tenant_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="部门不存在")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {
        "code": 200,
        "message": "删除成功"
    }
