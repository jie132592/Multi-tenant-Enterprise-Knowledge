"""
Token 使用统计模型
"""
from sqlalchemy import Column, String, Integer, BigInteger, Index
from sqlalchemy.orm import relationship, foreign

from app.models.base import BaseModel, TimestampModel


class TokenUsage(BaseModel, TimestampModel):
    """Token 使用统计表"""
    __tablename__ = "token_usage"

    tenant_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    session_id = Column(Integer, nullable=True, index=True)
    model = Column(String(64), nullable=False, comment="模型名称")
    prompt_tokens = Column(BigInteger, default=0, comment="提示词 token 数")
    completion_tokens = Column(BigInteger, default=0, comment="补全 token 数")
    total_tokens = Column(BigInteger, default=0, comment="总 token 数")

    # 多对一上层只读关联
    tenant = relationship(
        "Tenant",
        primaryjoin="TokenUsage.tenant_id == Tenant.id",
        foreign_keys=[tenant_id],
        viewonly=True,
        back_populates="token_usages"
    )
    session = relationship(
        "ChatSession",
        primaryjoin="TokenUsage.session_id == ChatSession.id",
        foreign_keys=[session_id],
        viewonly=True,
        back_populates="token_usages"
    )

    def __repr__(self):
        return f"<TokenUsage(id={self.id}, model={self.model}, total_tokens={self.total_tokens})>"
