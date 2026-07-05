"""
部门模型
"""
from sqlalchemy import Column, String, Integer, Index
from sqlalchemy.orm import relationship, foreign

from app.models.base import BaseModel, TimestampModel


class Department(BaseModel, TimestampModel):
    """部门表"""
    __tablename__ = "departments"

    tenant_id = Column(Integer, nullable=False, index=True)
    name = Column(String(128), nullable=False, comment="部门名称")
    code = Column(String(64), nullable=False, comment="部门编码")
    parent_id = Column(Integer, nullable=True, index=True)
    leader_user_id = Column(Integer, nullable=True, comment="部门负责人")
    description = Column(String(512), default="", comment="描述")

    # 联合唯一索引：同一租户下部门编码不能重复
    __table_args__ = (
        Index("uk_tenant_code", "tenant_id", "code", unique=True),
    )

    # ========== 多对一上层只读关联 ==========
    tenant = relationship(
        "Tenant",
        primaryjoin="Department.tenant_id == Tenant.id",
        foreign_keys=[tenant_id],
        viewonly=True,
        back_populates="departments"
    )
    # 上级部门（自关联多对一）
    parent = relationship(
        "Department",
        primaryjoin="Department.parent_id == Department.id",
        foreign_keys=[parent_id],
        remote_side="Department.id",
        viewonly=True,
        back_populates="children"
    )
    # 部门负责人用户
    leader = relationship(
        "User",
        primaryjoin="Department.leader_user_id == User.id",
        foreign_keys=[leader_user_id],
        viewonly=True,
        back_populates="led_departments"
    )

    # ========== 一对多集合，可增删、级联清理 ==========
    # 下级子部门
    children = relationship(
        "Department",
        primaryjoin="Department.id == foreign(Department.parent_id)",
        back_populates="parent",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )
    # 部门下所有用户
    users = relationship(
        "User",
        primaryjoin="Department.id == foreign(User.department_id)",
        back_populates="department",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )
    # 部门可见知识库
    knowledge_bases = relationship(
        "KnowledgeBase",
        primaryjoin="Department.id == foreign(KnowledgeBase.department_id)",
        back_populates="department",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Department(id={self.id}, name={self.name}, tenant_id={self.tenant_id})>"
