"""
认证服务
"""
from typing import Tuple, Optional

from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password, create_token_for_user
from app.models import User, Tenant


class AuthService:
    """认证服务"""

    def __init__(self, db: Session):
        self.db = db

    def register(
            self,
            tenant_name: str,
            tenant_code: str,
            username: str,
            email: str,
            password: str
    ) -> Tuple[Optional[User], Optional[str]]:
        """
        注册新用户（同时创建租户）
        :param tenant_name:
        :param tenant_code:
        :param username:
        :param email:
        :param password:
        :return:
            (User, None) 表示成功
            (None, error_message) 表示失败
        """
        # 检查租户编码是否已存在
        # query(Tenant) 查询的表是Tenant
        # filter(Tenant.code == tenant_code) 筛选 `tenants` 表中 `code` 字段等于传入的 `tenant_code`（租户编码）的数据
        # .first()只取查询到的第一条结果
        existing_tenant = self.db.query(Tenant).filter(Tenant.code == tenant_code).first()
        if existing_tenant:
            return None, "租户编码已存在"

        # 检查租户名称是否已存在
        existing_tenant_name = self.db.query(Tenant).filter(Tenant.name == tenant_name).first()
        if existing_tenant_name:
            return None, "租户名称已存在"

        # 创建租户
        # 实例化租户模型对象，准备插入数据库
        tenant = Tenant(
            name=tenant_name,
            code=tenant_code,
            status=1
        )
        # # 把租户对象添加到数据库会话，只是放入待提交队列，还没真正执行INSERT SQL
        self.db.add(tenant)
        # 刷新会话：立刻执行插入SQL，把数据写入数据库临时缓冲区，但不提交事务
        self.db.flush()
        # 此时：tenant.id 有值了，但是租户数据还没正式入库

        # 创建用户
        user = User(
            tenant_id=tenant.id,
            username=username,
            email=email,
            password=get_password_hash(password),
            is_active=1,
            is_super_admin=1 # 第一个设置为超级管理员
        )
        self.db.add(user)
        # 提交事务，租户+用户同时入库
        self.db.commit()
        # 刷新用户对象，拿到完整数据库字段用于返回
        self.db.refresh(user)

        return user, None

    def login(
            self,
            tenant_code: str,
            username: str,
            password: str
    ) -> Tuple[Optional[dict], Optional[str]]:
        """
        用户登录
        :param tenant_code:
        :param username:
        :param password:
        :return:
        """
        # 查找租户
        tenant = self.db.query(Tenant).filter(Tenant.code == tenant_code).first()
        if not tenant:
            return None, "租户不存在"

        if tenant.status != 1:
            return None, "租户已被禁用"

        # 查找用户
        user = self.db.query(User).filter(User.tenant_id == tenant.id, User.username == username).first()

        if not user:
            return None, "用户不存在"

        if user.is_active != 1:
            return None, "用户已被禁用"

        # 验证码
        if not verify_password(password, user.password):
            return None, "密码错误"

        # 更新最后的登陆时间
        from datetime import datetime
        user.last_login_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.db.commit()

        # 生成Token
        token_info = create_token_for_user(
            user_id=user.id,
            tenant_id=tenant.id,
            username=user.username,
        )

        return token_info, None

    def get_user_by_id(self, user_id: int, tenant_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return self.db.query(User).filter(
            User.id == user_id,
            User.tenant_id == tenant_id,
        ).first()

    def change_password(
            self,
            user_id: int,
            tenant_id: int,
            old_password: str,
            new_password: str
    ) -> Tuple[bool, Optional[str]]:
        """
        修改密码
        :param user_id:
        :param tenant_id:
        :param old_password:
        :param new_password:
        :return:
        """
        user = self.get_user_by_id(user_id, tenant_id)
        if not user:
            return False, "用户不存在"

        if not verify_password(old_password, user.password):
            return False, "旧密码错误"

        user.password = get_password_hash(new_password)
        self.db.commit()

        return True, None