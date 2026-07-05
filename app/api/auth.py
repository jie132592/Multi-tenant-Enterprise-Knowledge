from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app import get_db
from app.api.deps import get_current_user, CurrentUser
from app.schemas import RegisterRequest, UserResponse, BaseResponse, TokenResponse, LoginRequest, ChangePasswordRequest, UserListResponse, UserUpdateRequest
from app.services.auth import AuthService
from app.models import User, Department

router = APIRouter()

@router.post("/register", response_model=BaseResponse[UserResponse])
# Depends: FastAPI 的依赖注入工具，专门用来自动提供函数需要的对象，不用自己手动创建、关闭数据库连接
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    注册新用户
    同时创建对应的租户
    第一个用户自动成为租户管理员
    :param request:
    :param db:
    :return:
    """
    service = AuthService(db)
    user, error = service.register(
        tenant_name=request.tenant_name,
        tenant_code=request.tenant_code,
        username=request.username,
        email=request.email,
        password=request.password,
    )

    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return {
        "code": 200,
        "message": "成功",
        "data": UserResponse.model_validate(user)
    }

@router.post("/login", response_model=BaseResponse[TokenResponse])
def login(request: LoginRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    token_info, error = service.login(
        tenant_code=request.tenant_code,
        username=request.username,
        password=request.password,
    )
    if error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=error)

    return {
        "code": 200,
        "messages": "登录成功",
        "data": TokenResponse(**token_info)
    }

@router.get("/me", response_model=BaseResponse[UserResponse])
def get_current_user_info(current_user: CurrentUser = Depends(get_current_user)):
    """
    获取当前用户信息
    登录后才 获取
    :param current_user:
    :return:
    """
    return {
        "code": 200,
        "messages": "成功",
        "data": UserResponse.model_validate(current_user.user)
    }

@router.post("/change_password", response_model=BaseResponse)
def change_password(
        request: ChangePasswordRequest,
        current_user: CurrentUser = Depends(get_current_user),
        db: Session = Depends(get_db)):
    """
    修改密码

    - 需要登录后访问
    - 需要提供旧密码和新密码
    """
    service = AuthService(db)
    success, error = service.change_password(
        user_id=current_user.user_id,
        tenant_id=current_user.tenant_id,
        old_password=request.old_password,
        new_password=request.new_password,
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return {
        "code": 200,
        "messages": "密码修改成功"
    }


@router.get("/users", response_model=BaseResponse)
def list_users(
    keyword: str = None,
    page: int = 1,
    page_size: int = 20,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户列表

    - 超级管理员：可查看所有用户
    - 普通用户：仅可查看同租户用户
    """
    query = db.query(User)

    # 非超级管理员只能查看同租户用户
    if not current_user.user.is_super_admin:
        query = query.filter(User.tenant_id == current_user.tenant_id)

    # 关键词搜索
    if keyword:
        query = query.filter(
            (User.username.like(f"%{keyword}%")) |
            (User.email.like(f"%{keyword}%"))
        )

    # 获取总数
    total = query.count()

    # 分页
    offset = (page - 1) * page_size
    users = query.order_by(User.created_at.desc()).offset(offset).limit(page_size).all()

    # 构建返回数据
    result = []
    for user in users:
        # 获取部门名称
        department_name = None
        if user.department_id:
            dept = db.query(Department).filter(Department.id == user.department_id).first()
            if dept:
                department_name = dept.name

        result.append(UserListResponse(
            id=user.id,
            tenant_id=user.tenant_id,
            username=user.username,
            email=user.email,
            role=user.role or "member",
            is_active=user.is_active,
            is_super_admin=user.is_super_admin,
            is_tenant_admin=user.is_tenant_admin,
            department_id=user.department_id,
            department_name=department_name,
            last_login_at=user.last_login_at or "",
            created_at=user.created_at
        ))

    return {
        "code": 200,
        "message": "success",
        "data": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "list": result
        }
    }


@router.put("/users/{user_id}", response_model=BaseResponse)
def update_user(
    user_id: int,
    request: UserUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新用户信息（仅管理员）

    - 可以更新用户的部门、角色、状态等
    """
    from app.core.permissions import Permission, has_permission

    # 检查是否有用户管理权限
    if not has_permission(current_user.user.role, Permission.USER_MANAGE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要用户管理权限"
        )

    # 获取目标用户
    user = db.query(User).filter(
        User.id == user_id,
        User.tenant_id == current_user.tenant_id
    ).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    # 更新字段
    if request.role is not None:
        # 验证角色值
        valid_roles = ["super_admin", "tenant_admin", "member"]
        if request.role not in valid_roles:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"无效的角色，可选值: {valid_roles}")

        # 普通管理员不能设置 super_admin
        if request.role == "super_admin" and not current_user.user.is_super_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只有超级管理员可以设置超级管理员角色")

        user.role = request.role
        # 同步更新 is_tenant_admin 标志
        user.is_tenant_admin = 1 if request.role == "tenant_admin" else 0

    if request.department_id is not None:
        # 验证部门存在
        if request.department_id > 0:
            dept = db.query(Department).filter(
                Department.id == request.department_id,
                Department.tenant_id == current_user.tenant_id
            ).first()
            if not dept:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="部门不存在")
        user.department_id = request.department_id if request.department_id > 0 else None

    if request.is_active is not None:
        user.is_active = request.is_active

    db.commit()
    db.refresh(user)

    # 获取部门名称
    department_name = None
    if user.department_id:
        dept = db.query(Department).filter(Department.id == user.department_id).first()
        if dept:
            department_name = dept.name

    return {
        "code": 200,
        "message": "更新成功",
        "data": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "department_id": user.department_id,
            "department_name": department_name,
            "is_active": user.is_active
        }
    }