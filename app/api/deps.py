"""
API依赖项
"""
from typing import Optional

from fastapi import Depends, HTTPException, status
# Bearer Token认证工具，接收前端Authorization请求头
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# sqlalchemy数据库会话类型
from sqlalchemy.orm import Session

from app import get_db
from app.core.security import decode_access_token
from app.models import Tenant, User

# 实例化Bearer认证工具，用于读取请求头里的Token
security = HTTPBearer()

class CurrentUser:
    """当前登录用户封装类，一次性携带用户+租户全部信息"""
    def __init__(self, user: User, tenant: Tenant):
        self.user = user
        self.tenant = tenant
        self.user_id = user.id
        self.tenant_id = tenant.id
        self.username = user.username

def get_current_user(
        # 自动从请求头提取Bearer Token，无Token直接401
        credentials: HTTPAuthorizationCredentials = Depends(security),
        # 自动注入数据库会话
        db: Session = Depends(get_db)
) -> CurrentUser:
    """
    获取当前的登陆用户
    通过JWT Token验证用户身份，查询数据库，封装并返回当前用户对象
    :param credentials:
    :param db:
    :return:
    """
    # 取出Bearer后面的真实token字符串
    token = credentials.credentials

    # 解码、校验JWT令牌（校验签名、是否过期）
    payload = decode_access_token(token)
    # 解码失败、过期，payload为空
    if payload is None:
        # 抛出401未授权异常
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 无效或过期",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # 从token载荷取出用户ID、租户ID
    user_id = payload.get("user_id")
    tenant_id = payload.get("tenant_id")

    # 判断token里缺失用户、租户id，数据不合法
    if user_id is None or tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 数据不完整",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # 根据ID查询有效用户：匹配用户ID、所属租户ID、账户启用状态
    user = db.query(User).filter(
        User.id == user_id,
        User.tenant_id == tenant_id,
        User.is_active == 1
    ).first()

    # 查不到用户、账号已删除、禁用
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # 根据租户id查询租户信息
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    # 租户不存在
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="租户不存在",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # 校验租户启用状态：租户禁用禁止访问
    if tenant.status != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="租户已被禁用，请联系管理员"
        )

    return CurrentUser(user, tenant)

def get_current_user_optional(
    # auto_error=False：没有token不自动抛401，允许匿名访问
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    # 注入数据库会话
    db: Session = Depends(get_db)
) -> Optional[CurrentUser]:
    """可选的当前用户（某些接口不需要登录也能访问）"""
    # 请求头无token，直接返回空
    if credentials is None:
        return None

    try:
        # 有token就走完整登录校验逻辑
        return get_current_user(credentials=credentials, db=db)
    except HTTPException:
        # token错误、过期、用户禁用等校验失败、返回空、不拦截接口
        return None

def require_super_admin(
    # 先强制登录，拿到当前用户对象
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """权限校验：要求当前账号是超级管理员"""
    # 判断用户是否为超级管理员
    if not current_user.user.is_super_admin:
        # 403无权限
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限"
        )
    # 校验通过，放行用户信息给接口
    return current_user