"""用户模型"""
from sqlalchemy import Integer, Column, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app import Base
from app.models.base import TimestampModel


class User(Base, TimestampModel):
    """用户表"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete="CASCADE"), nullable=False, index=True)
    username = Column(String(64), nullable=False, comment="用户名")
    email = Column(String(128), nullable=False, comment="邮箱")
    password = Column(String(256), nullable=False, comment="密码")
    is_active = Column(Integer, default=1, comment="是否激活：1=是 0=否")
    is_super_admin = Column(Integer, default=0, comment="是否超级管理员: 1=是 0=否")
    last_login_at = Column(String(64), default="", comment="最后登录时间")

    # 关联关系 不生成数据库字段，仅代码层面查用
    # 关联租户模型Tenant，backref="users" 允许通过tenant.users查询该租户下所有用户
    # Tenant实例直接.user拿到该租户全部用户
    tenant = relationship("Tenant", backref="users")
    # 关联知识库模型, back_populates=双向绑定 lazy="dynamic"
    knowledge_bases = relationship("KnowledgeBase", back_populates="creator", lazy="dynamic")
    # 关联聊天会话模型，双向绑定，动态查询
    chat_sessions = relationship("ChatSession", back_populates="user", lazy="dynamic")

    # 表额外约束配置
    __table_args__ = (
        UniqueConstraint("tenant_id", "username", name="uk_tenant_username"),
    )

    # 打印用户对象
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, tenant_id={self.tenant_id})>"