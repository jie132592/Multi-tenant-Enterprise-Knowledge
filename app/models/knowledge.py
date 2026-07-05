"""
知识库相关模型
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Text, JSON, LargeBinary, Index
from sqlalchemy.orm import relationship, foreign

from app import Base
from app.models.base import TimestampModel, BaseModel


class VisibilityType:
    """可见性类型"""
    PUBLIC="public" # 全员可见
    DEPARTMENT="department" # 部门可见
    PRIVATE="private" # 仅创建者可见


class KnowledgeBase(BaseModel, TimestampModel):
    """知识库表"""
    __tablename__ = "knowledge_bases"

    tenant_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    department_id = Column(Integer, nullable=False, index=True)
    name = Column(String(256), nullable=False, comment="知识库名称")
    description = Column(Text, default="", comment="描述")
    status = Column(Integer, default=1, comment="状态: 1=正常 0=禁用")
    visibility = Column(String(32), default=VisibilityType.PRIVATE, comment="可见性: public/department/private")
    meta_data = Column(JSON, default=dict, comment="元数据")

    # ========== 多对一上层关联：只读viewonly=True ==========
    tenant = relationship(
        "Tenant",
        primaryjoin="KnowledgeBase.tenant_id == Tenant.id",
        foreign_keys=[tenant_id],
        back_populates="knowledge_bases",
        viewonly=True,
    )
    creator = relationship(
        "User",
        primaryjoin="KnowledgeBase.user_id == User.id",
        foreign_keys=[user_id],
        back_populates="knowledge_bases",
        viewonly=True,
    )
    department = relationship(
        "Department",
        primaryjoin="KnowledgeBase.department_id == Department.id",
        foreign_keys=[department_id],
        back_populates="knowledge_bases",
        viewonly=True,
    )

    # ========== 一对多文档集合：可增删、自动级联清理 ==========
    documents = relationship(
        "Document",
        primaryjoin="KnowledgeBase.id == foreign(Document.kb_id)",
        back_populates="knowledge_base",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )
    # 知识库的聊天会话
    chat_sessions = relationship(
        "ChatSession",
        primaryjoin="KnowledgeBase.id == foreign(ChatSession.kb_id)",
        back_populates="knowledge_base",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )


    def __repr__(self):
        return f"<KnowledgeBase(id={self.id}, name={self.name})>"


class Document(BaseModel, TimestampModel):
    """文档表"""
    __tablename__ = "documents"

    tenant_id = Column(Integer, nullable=False, index=True)
    kb_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    name = Column(String(512), nullable=False, comment="文档名称")
    content = Column(Text, default="", comment="原始内容")
    raw_content = Column(LargeBinary, nullable=True, comment="PDF 等二进制原始内容")
    char_length = Column(Integer, default=0, comment="字符数")
    status = Column(Integer, default=0, comment="处理状态: 0=待处理 1=处理中 2=完成 3=失败")
    error_message = Column(String(512), default="", comment="错误信息")
    meta_data = Column(JSON, default=dict, comment="元数据")

    # 索引
    __table_args__ = (
        Index("idx_kb_id", "kb_id"),
    )

    # 多对一上层只读关联
    tenant = relationship(
        "Tenant",
        primaryjoin="Document.tenant_id == Tenant.id",
        foreign_keys=[tenant_id],
        viewonly=True,
        back_populates="documents"
    )
    knowledge_base = relationship(
        "KnowledgeBase",
        primaryjoin="Document.kb_id == KnowledgeBase.id",
        foreign_keys=[kb_id],
        viewonly=True,
        back_populates="documents"
    )
    uploader = relationship(
        "User",
        primaryjoin="Document.user_id == User.id",
        foreign_keys=[user_id],
        viewonly=True,
        back_populates="documents",
    )

    # 一对多段落集合
    paragraphs = relationship(
        "Paragraph",
        primaryjoin="Document.id == foreign(Paragraph.doc_id)",
        back_populates="document",
        lazy="dynamic",
        cascade="all, delete-orphan",
        viewonly=True
    )

    def __repr__(self):
        return f"<Document(id={self.id}, name={self.name})>"


class Paragraph(BaseModel, TimestampModel):
    """段落表（分块后的内容）"""
    __tablename__ = "paragraphs"

    tenant_id = Column(Integer, nullable=False, index=True)
    doc_id = Column(Integer, nullable=False, index=True)
    content = Column(Text, nullable=False, comment="段落内容")
    position = Column(Integer, default=0, comment="位置序号")
    is_active = Column(Integer, default=1, comment="是否启用: 1=是 0=否")
    meta_data = Column(JSON, default=dict, comment="元数据，如来源位置等")

    # 索引
    __table_args__ = (
        Index("idx_doc_id", "doc_id"),
    )

    # 反向多对一，只读
    document = relationship(
        "Document",
        primaryjoin="foreign(Paragraph.doc_id) == Document.id",
        foreign_keys=[doc_id],
        back_populates="paragraphs",
        viewonly=True,
    )

    def __repr__(self):
        return f"<Paragraph(id={self.id}, doc_id={self.doc_id}, position={self.position})>"
