"""
对话相关模型
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship

from app import Base
from app.models.base import TimestampModel


class ChatSession(Base, TimestampModel):
    """对话会话表"""
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    kb_id = Column(Integer, ForeignKey("knowledge_bases.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(256), default="新对话", comment="会话标题")
    is_active = Column(Integer, default=1, comment="是否活跃: 1=是 0=否")

    # 关联关系
    tenant = relationship("Tenant", backref="chat_sessions")
    user = relationship("User", back_populates="chat_sessions")
    knowledge_base = relationship("KnowledgeBase", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ChatSession(id={self.id}, title={self.title})>"


class ChatMessage(Base, TimestampModel):
    """对话消息表"""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(32), nullable=False, comment="角色: user/assistant/system")
    content = Column(Text, nullable=False, comment="消息内容")
    meta = Column(JSON, default=dict, comment="扩展信息，如引用的段落列表")

    # 关联关系
    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, role={self.role}, session_id={self.session_id})>"
