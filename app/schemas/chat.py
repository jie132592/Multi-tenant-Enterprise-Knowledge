"""
对话相关 Pydantic 模型
"""
from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ChatMessageCreate(BaseModel):
    """发送消息请求"""
    content: str = Field(..., min_length=1, description="消息内容")
    kb_id: Optional[int] = Field(None, description="知识库ID，不传则使用会话绑定的知识库")


class ChatSessionCreate(BaseModel):
    """创建会话请求"""
    kb_id: int = Field(..., description="知识库ID")
    title: Optional[str] = Field(None, max_length=256, description="会话标题")


class ChatSessionResponse(BaseModel):
    """会话响应"""
    id: int
    tenant_id: int
    user_id: int
    kb_id: Optional[int] = None
    title: str
    is_active: int
    message_count: int = Field(default=0, description="消息数量")
    last_message: Optional[str] = ""
    last_message_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatMessageResponse(BaseModel):
    """消息响应"""
    id: int
    session_id: int
    role: str
    content: str
    meta: Optional[dict] = {}
    created_at: datetime

    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    """对话历史响应"""
    session: ChatSessionResponse
    messages: List[ChatMessageResponse]


class CitationItem(BaseModel):
    """引用项"""
    paragraph_id: int
    content: str
    score: float = Field(default=0.0, description="相似度分数")
    document_name: str = Field(default="", description="来源文档")


class ChatResponse(BaseModel):
    """对话响应"""
    answer: str = Field(..., description="AI 回答")
    citations: List[CitationItem] = Field(default_factory=list, description="引用列表")
    session_id: int
    message_id: int
