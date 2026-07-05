"""
对话相关模型
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Text, JSON, Index
from sqlalchemy.orm import relationship, foreign

from app import Base
from app.models.base import TimestampModel, BaseModel


class ChatSession(BaseModel, TimestampModel):
    """对话会话表"""
    __tablename__ = "chat_sessions"

    tenant_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    kb_id = Column(Integer, nullable=True, index=True)
    title = Column(String(256), default="新对话", comment="会话标题")
    is_active = Column(Integer, default=1, comment="是否活跃: 1=是 0=否")

    # ========== 多对一上层关联：只读，禁止通过会话修改归属 ==========
    tenant = relationship(
        "Tenant",
        # 手动指定两表连接条件，无FK时必填
        primaryjoin="ChatSession.tenant_id == Tenant.id",
        # 告诉ORM：当前模型这边用于关联的外键字段是tenant_id
        foreign_keys=[tenant_id],
        # 两张表的 `relationship` 双向绑定，让两边对象能互相访问，并且 ORM 缓存同步，不会出现数据不一致
        back_populates="chat_sessions",
        # 只读，禁止通过session.tenant修改、赋值
        viewonly=True
    )
    user = relationship(
        "User",
        primaryjoin="ChatSession.user_id == User.id",
        foreign_keys=[user_id],
        back_populates="chat_sessions",
        viewonly=True
    )
    knowledge_base = relationship(
        "KnowledgeBase",
        primaryjoin="ChatSession.kb_id == KnowledgeBase.id",
        foreign_keys=[kb_id],
        back_populates="chat_sessions",
        viewonly=True
    )

    # ========== 一对多子集合：可增删、自动级联清理 ==========
    # messages 变量名，给 ORM 双向绑定用
    messages = relationship(
        "ChatMessage",
        primaryjoin="ChatSession.id == foreign(ChatMessage.session_id)",
        lazy="dynamic",
        back_populates="session",
        cascade="all, delete-orphan",
    )
    token_usages = relationship(
        "TokenUsage",
        primaryjoin="ChatSession.id == foreign(TokenUsage.session_id)",
        lazy="dynamic",
        back_populates="session",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<ChatSession(id={self.id}, title={self.title})>"


class ChatMessage(BaseModel, TimestampModel):
    """对话消息表"""
    __tablename__ = "chat_messages"

    session_id = Column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(32), nullable=False, comment="角色: user/assistant/system")
    content = Column(Text, nullable=False, comment="消息内容")
    meta = Column(JSON, default=dict, comment="扩展信息，如引用的段落列表")

    # 表额外约束配置
    __table_args__ = (
        Index("idx_session_id", "session_id"),
    )

    # 反向多对一
    session = relationship(
        "ChatSession",
        primaryjoin="ChatMessage.session_id == ChatSession.id",
        foreign_keys=[session_id],
        back_populates="messages",
        viewonly=True
    )

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, role={self.role}, session_id={self.session_id})>"
