"""
知识库相关模型
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship

from app import Base
from app.models.base import TimestampModel


class KnowledgeBase(Base, TimestampModel):
    """知识库表"""
    __tablename__ = "knowledge_bases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(256), nullable=False, comment="知识库名称")
    description = Column(Text, default="", comment="描述")
    status = Column(Integer, default=1, comment="状态: 1=正常 0=禁用")
    meta_data = Column(JSON, default=dict, comment="元数据")

    # 关联关系
    tenant = relationship("Tenant", backref="knowledge_bases")
    creator = relationship("User", back_populates="knowledge_bases")
    documents = relationship("Document", back_populates="knowledge_base", lazy="dynamic", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="knowledge_base", lazy="dynamic")

    def __repr__(self):
        return f"<KnowledgeBase(id={self.id}, name={self.name})>"


class Document(Base, TimestampModel):
    """文档表"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    kb_id = Column(Integer, ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(512), nullable=False, comment="文档名称")
    content = Column(Text, default="", comment="原始内容")
    char_length = Column(Integer, default=0, comment="字符数")
    status = Column(Integer, default=0, comment="处理状态: 0=待处理 1=处理中 2=完成 3=失败")
    error_message = Column(String(512), default="", comment="错误信息")
    meta_data = Column(JSON, default=dict, comment="元数据")

    # 关联关系
    tenant = relationship("Tenant", backref="documents")
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    uploader = relationship("User")
    paragraphs = relationship("Paragraph", back_populates="document", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Document(id={self.id}, name={self.name})>"


class Paragraph(Base, TimestampModel):
    """段落表（分块后的内容）"""
    __tablename__ = "paragraphs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    doc_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False, comment="段落内容")
    position = Column(Integer, default=0, comment="位置序号")
    is_active = Column(Integer, default=1, comment="是否启用: 1=是 0=否")
    meta_data = Column(JSON, default=dict, comment="元数据，如来源位置等")

    # 关联关系
    tenant = relationship("Tenant", backref="paragraphs")
    document = relationship("Document", back_populates="paragraphs")

    def __repr__(self):
        return f"<Paragraph(id={self.id}, doc_id={self.doc_id}, position={self.position})>"
