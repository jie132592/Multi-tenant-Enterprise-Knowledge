"""文档服务"""
import io
import re
from typing import Optional, Tuple, List

from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.models import Document, Paragraph
from config import settings


class DocumentService:
    """文档服务"""

    def __init__(self, db: Session):
        self.db = db

    def create(
            self,
            tenant_id: int,
            kb_id: int,
            user_id: int,
            name: str,
            content: str,
            raw_content: bytes = None,
    ) -> Document:
        """创建文档"""
        doc = Document(
            tenant_id=tenant_id,
            kb_id=kb_id,
            user_id=user_id,
            name=name,
            content=content,
            raw_content=raw_content,
            char_length=len(content) if content else 0,
            status=0, # 待处理
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def get(
            self,
            doc_id: int,
            tenant_id: int,
    ) -> Optional[Document]:
        return self.db.query(Document).filter(
            Document.tenant_id == tenant_id,
            Document.id == doc_id,
        ).first()

    def list_by_kb(
            self,
            kb_id: int,
            tenant_id: int,
            page: int = 1,
            page_size: int = 10,
    ) -> Tuple[list[Document], int]:
        query = self.db.query(Document).filter(
            Document.kb_id == kb_id,
            Document.tenant_id == tenant_id,
        )

        total = query.count()
        docs = query.order_by(Document.created_at.desc())\
            .offset((page - 1) * page_size)\
            .limit(page_size).all()

        return docs, total

    def update_status(
            self,
            doc_id: int,
            status: int,
            error_msg: str = ""
    ) -> Optional[Document]:
        """更新文档状态"""
        doc = self.db.query(Document).filter(Document.id == doc_id).first()
        if doc:
            doc.status = status
            doc.error_message = error_msg
            self.db.commit()
            self.db.refresh(doc)
        return doc

    def delete(self, doc_id: int, tenant_id: int) -> bool:
        """删除文档"""
        doc = self.get(doc_id, tenant_id)
        if not doc:
            return False

        # 1. 删除所有段落
        self.db.query(Paragraph).filter(Paragraph.doc_id == doc_id).delete()

        # 2. 删除 文档
        self.db.delete(doc)
        self.db.commit()
        return True

    def get_paragraph_count(self, doc_id: int) -> int:
        """获取段落数量"""
        return self.db.query(Paragraph).filter(Paragraph.doc_id == doc_id).count()

class ParagraphService:
    """段落服务"""
    def __init__(self, db: Session):
        self.db = db

    def create_batch(
            self,
            tenant_id: int,
            doc_id: int,
            chunks: List[str]
    ):
        """批量创建段落"""
        paragraphs = []
        for i, chunk in enumerate(chunks):
            para = Paragraph(
                tenant_id=tenant_id,
                doc_id=doc_id,
                content=chunk,
                position=i,
                is_active=True
            )
            paragraphs.append(para)

        self.db.add_all(paragraphs)
        self.db.commit()

        for content in paragraphs:
            self.db.refresh(content)
        return paragraphs

    def delete_by_doc(self, doc_id: int) -> int:
        """删除文档的所有段落"""
        count = self.db.query(Paragraph).filter(
            Paragraph.doc_id == doc_id
        ).delete()
        self.db.commit()
        return count

    def get_active_by_doc(self, doc_id: int) -> List[Paragraph]:
        """获取文档的活跃段落"""
        return self.db.query(Paragraph).filter(
            Paragraph.doc_id == doc_id,
            Paragraph.is_active == 1
        ).order_by(Paragraph.position).all()