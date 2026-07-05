"""
对话服务
"""
from typing import Optional, Tuple, List

from sqlalchemy.orm import Session

from app.models import ChatSession, ChatMessage


class ChatService:
    """对话服务"""

    def __init__(self, db: Session):
        self.db = db

    def create_session(
            self,
            tenant_id: int,
            user_id: int,
            kb_id: int,
            title: str
    ) -> ChatSession:
        session = ChatSession(
            tenant_id=tenant_id,
            user_id=user_id,
            kb_id=kb_id,
            title=title or "新对话"
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session(self, session_id: int, tenant_id: int) -> Optional[ChatSession]:
        return self.db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.tenant_id == tenant_id).first()

    def list_sessions(
            self,
            tenant_id: int,
            user_id: int,
            kb_id: int = None,
            page: int = 1,
            page_size: int = 20
    ) -> Tuple[List[ChatSession], int]:
        """获取会话列表"""
        query = self.db.query(ChatSession).filter(
            ChatSession.tenant_id == tenant_id,
            ChatSession.user_id == user_id
        )

        if kb_id:
            query = query.filter(ChatSession.kb_id == kb_id)

        total = query.count()
        sessions = query.order_by(ChatSession.created_at.desc()) \
            .offset((page - 1) * page_size) \
            .limit(page_size) \
            .all()
        return sessions, total

    def get_messages(self, session_id: int):
        return self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at).all()

    def add_message(
            self,
            session_id: int,
            role: str,
            content: str,
            meta: dict = None
    ) -> ChatMessage:
        """添加消息"""
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            meta=meta
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def delete_session(self, session_id: int, tenant_id: int) -> bool:
        """删除消息"""
        session = self.get_session(session_id, tenant_id)
        if not session:
            return False
        # 删除消息
        self.db.query(ChatMessage).filter(ChatMessage.session_id == session).delete()
        # 删除会话
        self.db.delete(session)
        self.db.commit()
        return True

    def update_title(self, session_id: int, title: str) -> bool:
        """更新会话标题"""
        session = self.db.query(ChatSession).filter(
            ChatSession.id == session_id
        ).first()
        if session:
            session.title = title
            self.db.commit()
            return True
        return False