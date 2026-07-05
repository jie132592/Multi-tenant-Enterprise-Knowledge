"""知识库服务"""
from typing import Optional, Tuple, List

from sqlalchemy.orm import Session

from app.models import KnowledgeBase, Document, Paragraph, User


class KnowledgeService:
    """知识库服务"""

    def __init__(self, db: Session):
        self.db = db

    def create(
            self,
            tenant_id: int,
            user_id: int,
            name: str,
            description: str = "",
            visibility = "private",
            department_id: int = None,
    ):
        kn = KnowledgeBase(
            tenant_id=tenant_id,
            user_id=user_id,
            name=name,
            description=description,
            status=1,
            visibility=visibility,
            department_id=department_id
        )
        self.db.add(kn)
        self.db.commit()
        self.db.refresh(kn)
        return kn

    def get(self, kb_id: int, tenant_id: int) -> Optional[KnowledgeBase]:
        """获取知识库详情"""
        return self.db.query(KnowledgeBase).filter(
            KnowledgeBase.tenant_id == tenant_id,
            KnowledgeBase.id == kb_id
        ).first()

    def list(
            self,
            tenant_id: int,
            page: int = 1,
            page_size: int = 10,
            keyword: str = "",
            user_id: int = None,
            user_department_id: int = None,
    ) -> Tuple[List[KnowledgeBase], int]:
        """
        获取知识库列表

        Args:
            tenant_id: 租户 ID
            page: 页码
            page_size: 每页数量
            keyword: 搜索关键字
            user_id: 当前用户 ID（用于判断私有知识库）
            user_department_id: 用户所属部门 ID（用于判断部门知识库）
        """
        # 1. 只构建查询，不访问数据库
        query = self.db.query(KnowledgeBase).filter(
            KnowledgeBase.tenant_id == tenant_id,
        )
        # 权限过滤
        # 有用户ID，继续追加权限过滤，还是不查库
        if user_id:
            # 创建者总是能看到自己创建的知识库
            # 非创建者的用户，只能看 public 和 department 可见的知识库
            query = query.filter(
                (KnowledgeBase.user_id == user_id) |
                (KnowledgeBase.visibility == "public") |
                (KnowledgeBase.visibility == "department") & (KnowledgeBase.department_id == user_department_id)
            )
        # 3. 有关键词，继续叠加模糊条件
        if keyword:
            query = query.filter(KnowledgeBase.name.like(f"%{keyword}%"))

        total = query.count()

        kb = query.order_by(KnowledgeBase.created_at.desc())\
            .offset((page - 1) * page_size)\
            .limit(page_size).all()

        return kb, total


    def update(
        self,
        kb_id: int,
        tenant_id: int,
        name: str = None,
        description: str = None,
        status: int = None,
        visibility: str = None,
        department_id: int = None
    ) -> Optional[KnowledgeBase]:
        """更新知识库"""
        kb = self.get(kb_id, tenant_id)
        if not kb:
            return None

        if name is not None:
            kb.name = name
        if description is not None:
            kb.description = description
        if status is not None:
            kb.status = status
        if visibility is not None:
            kb.visibility = visibility
        if department_id is not None:
            kb.department_id = department_id

        self.db.commit()
        self.db.refresh(kb)
        return kb

    def delete(self, kb_id: int, tenant_id: int) -> bool:
        """删除知识库（包含级联删除文档和段落）"""
        kb = self.get(kb_id, tenant_id)
        if not kb:
            return False
        # 1. 获取所有文档 ID
        docs = self.db.query(Document).filter(Document.kb_id == kb_id).all()
        doc_ids = [doc.id for doc in docs]
        # 删除所有段落
        if doc_ids:
            self.db.query(Paragraph).filter(Paragraph.doc_id.in_(doc_ids)).delete()

        # 删除所有文档
        self.db.query(Document).filter(Document.kb_id == kb_id).delete()

        # 删除知识库
        self.db.delete(kb)
        self.db.commit()
        return True

    def get_document_count(self, kb_id: int) -> int:
        """获取文档数量"""
        return self.db.query(Document).filter(Document.kb_id == kb_id).count()

    def get_paragraph_count(self, kb_id: int) -> int:
        """获取段落数量"""
        return self.db.query(Paragraph).filter(
            Paragraph.doc_id.in_(
                self.db.query(Document.id).filter(Document.kb_id == kb_id)
            )
        ).count()

    def get_creator_username(self, user_id: int) -> str:
        """获取创建者用户名"""
        user = self.db.query(User).filter(User.id == user_id).first()
        return user.username if user else ""