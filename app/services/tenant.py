"""租户服务"""
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Tenant, TokenUsage, ChatSession, ChatMessage, Document, Paragraph, KnowledgeBase, Department, \
    User


class TenantService:
    """租户服务"""

    def __init__(self, db: Session):
        self.db = db

    def get(self, tenant_id: int) -> Optional[Tenant]:
        """获取租户id"""
        return self.db.query(Tenant).filter(Tenant.id == tenant_id).first()

    def get_by_code(self, code: str) -> Optional[Tenant]:
        """根据编码获取租户"""
        return self.db.query(Tenant).filter(Tenant.code == code).first()

    def delete(self, tenant_id: int) -> bool:
        """
        删除租户（包含级联删除）
        """
        tenant = self.get(tenant_id)
        if not tenant:
            return False

        # 1. 删除所有 TokenUsage
        self.db.query(TokenUsage).filter(TokenUsage.tenant_id == tenant_id).delete()

        # 2. 删除所有 ChatMessage (通过 ChatSession)
        sessions = self.db.query(ChatSession).filter(ChatSession.tenant_id == tenant_id).all()
        session_ids = [s.id for s in sessions]
        if session_ids:
            self.db.query(ChatMessage).filter(ChatMessage.session_id.in_(session_ids)).delete()

        # 3. 删除所有 ChatSession
        self.db.query(ChatSession).filter(ChatSession.tenant_id == tenant_id).delete()

        # 4. 删除所有 Paragraph (通过 Document)
        docs = self.db.query(Document).filter(Document.tenant_id == tenant_id).all()
        doc_ids = [d.id for d in docs]
        if doc_ids:
            self.db.query(Paragraph).filter(Paragraph.doc_id.in_(doc_ids)).delete()

        # 5. 删除所有 Document
        self.db.query(Document).filter(Document.tenant_id == tenant_id).delete()

        # 6. 删除所有 KnowledgeBase
        self.db.query(KnowledgeBase).filter(KnowledgeBase.tenant_id == tenant_id).delete()

        # 7. 删除所有 Department
        self.db.query(Department).filter(Department.tenant_id == tenant_id).delete()

        # 8. 删除所有 User
        self.db.query(User).filter(User.tenant_id == tenant_id).delete()

        # 9. 删除租户
        self.db.delete(tenant)
        self.db.commit()
        return True