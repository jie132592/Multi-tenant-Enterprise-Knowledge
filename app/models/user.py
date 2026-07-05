"""
用户模型
"""
from sqlalchemy import Column, String, Integer, Index
from sqlalchemy.orm import relationship, foreign

from app.models.base import BaseModel, TimestampModel


class UserRole:
    """用户角色常量"""
    SUPER_ADMIN = "super_admin"      # 超级管理员（系统级）
    TENANT_ADMIN = "tenant_admin"    # 租户管理员
    MEMBER = "member"                # 普通成员


class User(BaseModel, TimestampModel):
    """用户表"""
    __tablename__ = "users"

    tenant_id = Column(Integer, nullable=False, index=True)
    department_id = Column(Integer, nullable=True, index=True)
    username = Column(String(64), nullable=False, comment="用户名")
    email = Column(String(128), nullable=False, comment="邮箱")
    password = Column(String(256), nullable=False, comment="密码hash")
    role = Column(String(32), default=UserRole.MEMBER, comment="角色: super_admin/tenant_admin/member")
    is_active = Column(Integer, default=1, comment="是否激活: 1=是 0=否")
    is_super_admin = Column(Integer, default=0, comment="是否超级管理员: 1=是 0=否")
    is_tenant_admin = Column(Integer, default=0, comment="是否租户管理员: 1=是 0=否")
    last_login_at = Column(String(64), default="", comment="最后登录时间")

    # 联合唯一索引：同一个租户内用户名不能重复
    __table_args__ = (
        Index("uk_tenant_username", "tenant_id", "username", unique=True),
    )

    # ========== 多对一上层只读关联 ==========
    tenant = relationship(
        "Tenant",
        primaryjoin="User.tenant_id == Tenant.id",
        foreign_keys=[tenant_id],
        viewonly=True,
        back_populates="users"
    )
    department = relationship(
        "Department",
        primaryjoin="User.department_id == Department.id",
        foreign_keys=[department_id],
        viewonly=True,
        back_populates="users"
    )

    # ========== 一对多集合，可增删、自动级联删除 ==========
    # 用户创建的知识库
    knowledge_bases = relationship(
        "KnowledgeBase",
        primaryjoin="User.id == foreign(KnowledgeBase.user_id)",
        back_populates="creator",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )
    # 用户上传的文档
    documents = relationship(
        "Document",
        primaryjoin="User.id == foreign(Document.user_id)",
        back_populates="uploader",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )
    # 用户作为负责人的部门
    led_departments = relationship(
        "Department",
        primaryjoin="User.id == foreign(Department.leader_user_id)",
        back_populates="leader",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )
    # 用户的聊天会话
    chat_sessions = relationship(
        "ChatSession",
        primaryjoin="User.id == foreign(ChatSession.user_id)",
        back_populates="user",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, tenant_id={self.tenant_id}, role={self.role})>"
