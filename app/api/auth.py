from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import get_db
from app.api.deps import get_current_user, CurrentUser
from app.schemas import RegisterRequest, UserResponse, BaseResponse, TokenResponse, LoginRequest, ChangePasswordRequest
from app.services.auth import AuthService

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